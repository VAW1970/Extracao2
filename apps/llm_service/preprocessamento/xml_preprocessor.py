"""
XML Preprocessor — parses XML files using lxml (preferred for performance and namespace support).

Falls back to stdlib xml.etree.ElementTree if lxml is not available.
Primarily used for NF-e (Nota Fiscal Eletrônica) XML parsing.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

logger = logging.getLogger("apps.llm_service")


class XMLPreprocessor:
    """Parse and extract structured data from XML files."""

    def preprocess(self, file_path: str | Path | BytesIO) -> dict:
        """Preprocess an XML file.

        Args:
            file_path: Path to the XML file or a BytesIO stream.
        """
        # Try lxml first (better namespace support), fallback to stdlib
        try:
            from lxml import etree as ET
            USE_LXML = True
        except ImportError:
            import xml.etree.ElementTree as ET
            USE_LXML = False

        result = {
            "text": None,
            "root_tag": None,
            "element_count": 0,
            "parsed_data": {},
        }

        try:
            if USE_LXML:
                # lxml parser with recovery option for malformed XML
                parser = ET.XMLParser(recover=True, encoding="utf-8")
                tree = ET.parse(file_path, parser)
            else:
                tree = ET.parse(file_path)
            root = tree.getroot()

            result["root_tag"] = root.tag
            result["element_count"] = len(list(root.iter()))

            # Get the full XML text
            if USE_LXML:
                result["text"] = ET.tostring(root, encoding="unicode", pretty_print=True)
            else:
                result["text"] = ET.tostring(root, encoding="unicode")

            # Parse common NF-e fields
            result["parsed_data"] = self._parse_nfe(root, USE_LXML)

            logger.info(
                f"XML preprocessed: root={result['root_tag']}, "
                f"{result['element_count']} elements (lxml={USE_LXML})"
            )

        except ET.ParseError as e:
            logger.error(f"Invalid XML syntax in {file_path}: {e}")
            raise ValueError(f"Invalid XML: {e}")
        except Exception as e:
            logger.error(f"Error preprocessing XML {file_path}: {e}")
            raise

        return result

    def _parse_nfe(self, root, use_lxml: bool) -> dict[str, Any]:
        """Extract common NF-e fields from the XML tree.

        Handles the Brazilian NF-e XML namespace.
        """
        data = {}

        # Get namespace map (lxml has nsmap, stdlib doesn't)
        if use_lxml:
            nsmap = root.nsmap
        else:
            # Extract namespace from root tag if possible
            nsmap = {}
            if "}" in root.tag:
                ns_uri = root.tag.split("}")[0][1:]
                nsmap[None] = ns_uri  # default namespace

        # Common NF-e namespace
        nfe_ns = "http://www.portalfiscal.inf.br/nfe"

        # Helper to find elements with namespace
        def find_elems(tag_name):
            if use_lxml:
                return root.iter(f"{{{nfe_ns}}}{tag_name}")
            else:
                # stdlib: iterate and match local name
                return (e for e in root.iter() if e.tag.split("}")[-1] == tag_name)

        # Try to extract common fields regardless of namespace
        field_map = {
            "cNF": "numero_nfe",
            "natOp": "natureza_operacao",
            "mod": "modelo",
            "serie": "serie",
            "nNF": "numero",
            "dhEmi": "data_emissao",
            "tpAmb": "ambiente",
            "CNPJ": "cnpj",
            "xNome": "razao_social",
            "IE": "inscricao_estadual",
            "vProd": "valor_produto",
            "vNF": "valor_total",
            "vDesc": "valor_desconto",
            "vICMS": "valor_icms",
            "vIPI": "valor_ipi",
            "vPIS": "valor_pis",
            "vCOFINS": "valor_cofins",
            "chNFe": "chave_acesso",
            "infProt": "protocolo",
        }

        # Search in NF-e namespace first, then fallback to any
        for tag_name, field_key in field_map.items():
            elements = list(find_elems(tag_name))
            if not elements:
                # Fallback: search without namespace
                for elem in root.iter():
                    local_tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                    if local_tag == tag_name and elem.text:
                        elements = [elem]
                        break

            for elem in elements:
                if elem.text and elem.text.strip():
                    data[field_key] = elem.text.strip()
                    break  # Take first match

        return data
