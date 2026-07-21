"""
Schema validation for LLM extraction output.

Uses pydantic to validate that extracted data matches the expected schema
before persisting to the database. Monetary fields are validated and
converted to ensure proper Decimal handling.
"""

import json
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, ValidationError

logger = logging.getLogger("apps.llm_service")

SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"


class BaseExtracaoSchema(BaseModel):
    """Base schema for all document type extractions."""

    @field_validator("*", mode="before")
    @classmethod
    def clean_string_fields(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class NotaFiscalSchema(BaseExtracaoSchema):
    """Schema for Nota Fiscal extraction."""

    numero: str
    serie: str | None = None
    cnpj_emitente: str | None = None
    cnpj_destinatario: str | None = None
    data_emissao: str | None = None
    valor_total: str | None = None
    itens: list[dict] = Field(default_factory=list)
    chave_acesso: str | None = None

    @field_validator("valor_total")
    @classmethod
    def validate_valor(cls, v):
        if v is not None:
            try:
                Decimal(str(v).replace(",", "."))
            except InvalidOperation:
                raise ValueError(f"Valor monetário inválido: {v}")
        return v


class ContratoSchema(BaseExtracaoSchema):
    """Schema for Contrato extraction."""

    partes_envolvidas: list[str] = Field(default_factory=list)
    objeto: str | None = None
    valor: str | None = None
    data_inicio: str | None = None
    data_fim: str | None = None
    forma_pagamento: str | None = None

    @field_validator("valor")
    @classmethod
    def validate_valor(cls, v):
        if v is not None:
            try:
                Decimal(str(v).replace(",", "."))
            except InvalidOperation:
                raise ValueError(f"Valor monetário inválido: {v}")
        return v


class DemonstrativoSchema(BaseExtracaoSchema):
    """Schema for Demonstrativo extraction."""

    periodo_referencia: str | None = None
    categorias: list[dict] = Field(default_factory=list)
    saldo: str | None = None


class BoletoSchema(BaseExtracaoSchema):
    """Schema for Boleto extraction."""

    linha_digitavel: str | None = None
    valor: str | None = None
    data_vencimento: str | None = None
    beneficiario: str | None = None
    pagador: str | None = None

    @field_validator("valor")
    @classmethod
    def validate_valor(cls, v):
        if v is not None:
            try:
                Decimal(str(v).replace(",", "."))
            except InvalidOperation:
                raise ValueError(f"Valor monetário inválido: {v}")
        return v


# Registry of schemas by document type
SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "nota_fiscal": NotaFiscalSchema,
    "contrato": ContratoSchema,
    "demonstrativo": DemonstrativoSchema,
    "boleto": BoletoSchema,
}


def load_schema_from_file(tipo_documento: str) -> dict | None:
    """Load a JSON schema from the schemas/ directory."""
    schema_path = SCHEMAS_DIR / f"{tipo_documento}.json"
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def validate_extraction(tipo_documento: str, dados: dict) -> tuple[bool, dict | str]:
    """Validate extracted data against the expected schema.

    Args:
        tipo_documento: The document type key.
        dados: The extracted data dictionary.

    Returns:
        Tuple of (is_valid, validated_data_or_error_message).
    """
    schema_class = SCHEMA_REGISTRY.get(tipo_documento)
    if not schema_class:
        return False, f"Unknown document type: {tipo_documento}"

    try:
        validated = schema_class(**dados)
        # Return the validated data as a dict, converting Decimal fields
        validated_dict = validated.model_dump()
        logger.info(f"Schema validation passed for {tipo_documento}")
        return True, validated_dict

    except ValidationError as e:
        error_msg = str(e)
        logger.warning(f"Schema validation failed for {tipo_documento}: {error_msg}")
        return False, error_msg


def _try_convert_to_decimal(value: Any) -> Decimal | None:
    """Try to convert a value to Decimal, handling Brazilian comma format."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        has_comma = "," in text
        has_dot = "." in text
        if has_comma and has_dot:
            # Brazilian format: 1.500,00 → 1500.00
            cleaned = text.replace(".", "").replace(",", ".")
        elif has_comma:
            # Likely Brazilian decimal: 1500,00 → 1500.00
            cleaned = text.replace(",", ".")
        else:
            # Standard format: 1500.00 or 1500
            cleaned = text
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
    return None


def convert_monetary_fields(dados: dict) -> dict:
    """Convert monetary string fields to Decimal for storage.

    This is a safety net to ensure all monetary values are properly
    converted before database storage.
    """
    monetary_fields = [
        "valor_total", "valor", "saldo", "valor_produto",
        "valor_desconto", "valor_icms", "valor_ipi",
        "valor_pis", "valor_cofins",
        "valor_unitario",
    ]

    converted = dados.copy()
    for field in monetary_fields:
        if field in converted and converted[field] is not None:
            result = _try_convert_to_decimal(converted[field])
            if result is not None:
                converted[field] = result
            else:
                logger.warning(f"Could not convert {field}={converted[field]} to Decimal")

    # Handle nested items
    for key in ("itens", "categorias"):
        if key in converted and isinstance(converted[key], list):
            converted[key] = [
                convert_monetary_fields(item) if isinstance(item, dict) else item
                for item in converted[key]
            ]

    return converted
