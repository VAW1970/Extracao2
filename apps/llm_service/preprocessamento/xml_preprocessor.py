"""
XML Preprocessor — parses XML files using xml.etree.ElementTree (stdlib).

No external dependencies required — uses Python's built-in XML parsing.
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
        import xml.etree.ElementTree as ET

        result = {
            "text": None,
            "root_tag": None,
            "element_count": 0,
            "parsed_data": {},
        }

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            result["root_tag"] = root.tag
            result["element_count"] = len(list(root.iter()))

            # Get the full XML text
            result["text"] = ET.tostring(root, encoding="unicode")

            # Parse common NF-e fields
            result["parsed_data"] = self._parse_nfe(root)

            logger.info(
                f"XML preprocessed: root={result['root_tag']}, "
                f"{result['element_count']} elements"
            )

        except ET.ParseError as e:
            logger.error(f"Invalid XML syntax in {file_path}: {e}")
            raise ValueError(f"Invalid XML: {e}")
        except Exception as e:
            logger.error(f"Error preprocessing XML {file_path}: {e}")
            raise

        return result

    def _parse_nfe(self, root) -> dict[str, Any]:
        """Extract common NF-e fields from the XML tree.

        Handles the Brazilian NF-e XML namespace.
        """
        data = {}
        nsmap = root.nsmap

        # Try to extract common fields regardless of namespace
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            # Common NF-e fields
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

            if tag in field_map and elem.text:
                data[field_map[tag]] = elem.text.strip()

        return data
