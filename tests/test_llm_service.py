"""
Tests for the LLM service layer.
Uses MockProvider to avoid real network calls.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from apps.llm_service.provider_factory import MockProvider, get_llm_provider
from apps.llm_service.provider_base import LLMExtractionError
from apps.llm_service.validacao_schema import (
    validate_extraction,
    convert_monetary_fields,
    NotaFiscalSchema,
)


class TestMockProvider:
    """Tests for the MockProvider."""

    def test_mock_provider_returns_expected_response(self):
        mock_data = {"numero": "12345", "valor_total": "1500.00"}
        provider = MockProvider(mock_response=mock_data)
        result = provider.extrair("test content", "test prompt", {})

        assert result["numero"] == "12345"
        assert result["valor_total"] == "1500.00"
        assert result["_metadata"]["provider"] == "mock"

    def test_mock_provider_name(self):
        provider = MockProvider()
        assert provider.get_provider_name() == "mock"
        assert provider.get_model_name() == "mock-model"


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_valid_nota_fiscal(self):
        data = {
            "numero": "12345",
            "serie": "1",
            "valor_total": "1500.00",
        }
        is_valid, result = validate_extraction("nota_fiscal", data)
        assert is_valid is True
        assert result["numero"] == "12345"

    def test_invalid_schema_returns_error(self):
        data = {}  # Missing required "numero" field
        is_valid, result = validate_extraction("nota_fiscal", data)
        assert is_valid is False
        assert "numero" in result  # Error message mentions the missing field

    def test_unknown_document_type(self):
        is_valid, result = validate_extraction("unknown_type", {})
        assert is_valid is False
        assert "Unknown document type" in result

    def test_monetary_field_validation(self):
        data = {
            "numero": "12345",
            "valor_total": "invalid-money",
        }
        is_valid, result = validate_extraction("nota_fiscal", data)
        assert is_valid is False


class TestConvertMonetaryFields:
    """Tests for monetary field conversion."""

    def test_convert_simple_fields(self):
        data = {"valor_total": "1500.00", "valor": "2000.50"}
        result = convert_monetary_fields(data)
        from decimal import Decimal
        assert result["valor_total"] == Decimal("1500.00")
        assert result["valor"] == Decimal("2000.50")

    def test_convert_comma_decimal(self):
        data = {"valor_total": "1.500,00"}
        result = convert_monetary_fields(data)
        from decimal import Decimal
        assert result["valor_total"] == Decimal("1500.00")

    def test_convert_nested_items(self):
        data = {
            "itens": [
                {"valor_unitario": "10.00", "valor_total": "20.00"},
                {"valor_unitario": "5.50", "valor_total": "11.00"},
            ]
        }
        result = convert_monetary_fields(data)
        from decimal import Decimal
        assert result["itens"][0]["valor_unitario"] == Decimal("10.00")
        assert result["itens"][1]["valor_total"] == Decimal("11.00")

    def test_convert_none_values(self):
        data = {"valor_total": None}
        result = convert_monetary_fields(data)
        assert result["valor_total"] is None
