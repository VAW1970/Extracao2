"""
Extraction Service — orchestrates the full extraction pipeline.

Pipeline: pre-processamento → prompt → chamada LLM → validação → persistência
"""

import json
import logging
import time
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.documentos.models import Documento, DadosExtraidos

from .preprocessamento.pdf_preprocessor import PDFPreprocessor
from .preprocessamento.xml_preprocessor import XMLPreprocessor
from .preprocessamento.image_preprocessor import ImagePreprocessor
from .provider_factory import MockProvider, get_llm_provider
from .provider_base import LLMExtractionError
from .validacao_schema import validate_extraction, convert_monetary_fields

logger = logging.getLogger("apps.llm_service")

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def load_prompt_template(tipo_documento: str) -> str:
    """Load the prompt template for a given document type."""
    prompt_path = PROMPTS_DIR / f"{tipo_documento}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def preprocess_document(documento: Documento) -> dict[str, Any]:
    """Pre-process a document based on its format.

    Returns:
        dict with keys:
            - content: extracted text or bytes
            - is_multimodal: whether the content is for a vision model
            - metadata: additional preprocessing info
    """
    # Open via Django storage backend (downloads from Supabase in production).
    # Use .open() which returns a file-like object the pre-processors can read.
    file_obj = documento.arquivo_original.open("rb")
    file_bytes = file_obj.read()
    file_obj.close()

    if documento.formato_arquivo == Documento.FormatoArquivo.PDF:
        preprocessor = PDFPreprocessor()
        result = preprocessor.preprocess(BytesIO(file_bytes))

        if result["is_scanned"]:
            # Scanned PDF — use multimodal LLM
            return {
                "content": file_bytes,
                "is_multimodal": True,
                "metadata": result,
            }
        else:
            # Text-based PDF — use text extraction
            return {
                "content": result["text"],
                "is_multimodal": False,
                "metadata": result,
            }

    elif documento.formato_arquivo == Documento.FormatoArquivo.XML:
        preprocessor = XMLPreprocessor()
        result = preprocessor.preprocess(BytesIO(file_bytes))
        return {
            "content": result["text"],
            "is_multimodal": False,
            "metadata": result,
        }

    elif documento.formato_arquivo == Documento.FormatoArquivo.IMAGEM:
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(
            BytesIO(file_bytes),
            original_name=documento.arquivo_original.name,
        )
        return {
            "content": result["image_bytes"],
            "is_multimodal": True,
            "metadata": result,
        }

    else:
        raise ValueError(f"Unsupported document format: {documento.formato_arquivo}")


def extrair_dados(
    documento_id: int,
    testing: bool = False,
) -> DadosExtraidos | None:
    """Execute the full extraction pipeline for a document.

    Args:
        documento_id: ID of the Documento to process.
        testing: If True, uses MockProvider.

    Returns:
        DadosExtraidos instance or None if extraction fails.
    """
    try:
        documento = Documento.objects.get(pk=documento_id)
    except Documento.DoesNotExist:
        logger.error(f"Documento {documento_id} not found")
        return None

    max_retries = settings.EXTRACTION_MAX_RETRIES
    provider = get_llm_provider(testing=testing)

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                f"Extraction attempt {attempt}/{max_retries} "
                f"for document {documento_id}"
            )

            # Step 1: Pre-process the document
            preprocessed = preprocess_document(documento)

            # Step 2: Load prompt template
            prompt_template = load_prompt_template(documento.tipo_documento)

            # Step 3: Call the LLM
            extracted = provider.extrair(
                conteudo_documento=preprocessed["content"],
                prompt_template=prompt_template,
                schema_esperado={},
                is_multimodal=preprocessed["is_multimodal"],
            )

            # Step 4: Validate against schema
            is_valid, result = validate_extraction(documento.tipo_documento, extracted)

            if is_valid:
                # Step 5: Convert monetary fields and persist
                dados_finais = convert_monetary_fields(result)

                # Remove _metadata before storing
                metadata = dados_finais.pop("_metadata", {})

                dados_extraidos = DadosExtraidos.objects.create(
                    documento=documento,
                    campos_extraidos=dados_finais,
                    provedor_llm_utilizado=metadata.get("provider", provider.get_provider_name()),
                    modelo_llm_utilizado=metadata.get("model", provider.get_model_name()),
                    tempo_resposta_ms=metadata.get("tempo_resposta_ms"),
                    tokens_utilizados=metadata.get("tokens_utilizados"),
                    tentativas_realizadas=attempt,
                    precisa_revisao=False,
                )

                logger.info(
                    f"Extraction successful for document {documento_id} "
                    f"on attempt {attempt}"
                )
                return dados_extraidos
            else:
                # Validation failed — retry with error feedback
                if attempt < max_retries:
                    # Also remove _metadata from the raw response for retry
                    raw_for_retry = extracted.copy()
                    raw_for_retry.pop("_metadata", None)
                    logger.warning(
                        f"Validation failed on attempt {attempt}: {result}. Retrying..."
                    )
                    continue
                else:
                    # All attempts exhausted — mark as needing review
                    logger.error(
                        f"All {max_retries} attempts exhausted for document {documento_id}"
                    )
                    # Remove _metadata before storing raw response
                    raw_for_audit = extracted.copy()
                    raw_for_audit.pop("_metadata", None)
                    dados_extraidos = DadosExtraidos.objects.create(
                        documento=documento,
                        campos_extraidos=raw_for_audit,
                        provedor_llm_utilizado=provider.get_provider_name(),
                        modelo_llm_utilizado=provider.get_model_name(),
                        tentativas_realizadas=attempt,
                        precisa_revisao=True,
                        resposta_bruta_llm=json.dumps(raw_for_audit, ensure_ascii=False),
                    )
                    return dados_extraidos

        except LLMExtractionError as e:
            logger.error(f"LLM extraction error on attempt {attempt}: {e}")
            if attempt >= max_retries:
                # Create a record with the error for audit
                DadosExtraidos.objects.create(
                    documento=documento,
                    campos_extraidos={},
                    provedor_llm_utilizado=provider.get_provider_name(),
                    modelo_llm_utilizado=provider.get_model_name(),
                    tentativas_realizadas=attempt,
                    precisa_revisao=True,
                    resposta_bruta_llm=f"ERROR: {str(e)}",
                )
                return None
            continue

    return None
