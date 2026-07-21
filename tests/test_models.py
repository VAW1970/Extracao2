"""
Unit tests for Django models.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.documentos.models import Documento, DadosExtraidos
from apps.validacao.models import LancamentoPreparado, ValidacaoLog

Usuario = get_user_model()


@pytest.mark.django_db
class TestUsuario:
    """Tests for the custom Usuario model."""

    def test_create_usuario(self):
        user = Usuario.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")

    def test_create_superuser(self):
        admin = Usuario.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_usuario_str_with_full_name(self):
        user = Usuario.objects.create_user(
            username="testuser",
            first_name="João",
            last_name="Silva",
        )
        assert str(user) == "João Silva"

    def test_usuario_str_without_full_name(self):
        user = Usuario.objects.create_user(username="testuser")
        assert str(user) == "testuser"


@pytest.mark.django_db
class TestDocumento:
    """Tests for the Documento model."""

    def test_create_documento(self, usuario):
        doc = Documento.objects.create(
            tipo_documento=Documento.TipoDocumento.NOTA_FISCAL,
            formato_arquivo=Documento.FormatoArquivo.PDF,
            arquivo_original="documentos/test.pdf",
            origem="upload_manual",
            criado_por=usuario,
        )
        assert doc.tipo_documento == "nota_fiscal"
        assert doc.status == "pendente"
        assert doc.criado_por == usuario

    def test_documento_str(self, usuario):
        doc = Documento.objects.create(
            tipo_documento=Documento.TipoDocumento.CONTRATO,
            formato_arquivo=Documento.FormatoArquivo.PDF,
            arquivo_original="documentos/contrato.pdf",
            origem="upload_manual",
            criado_por=usuario,
        )
        assert "Contrato" in str(doc)


@pytest.mark.django_db
class TestLancamentoPreparado:
    """Tests for LancamentoPreparado model — critical constraints."""

    def test_create_lancamento_with_required_fields(self, usuario):
        doc = Documento.objects.create(
            tipo_documento=Documento.TipoDocumento.BOLETO,
            formato_arquivo=Documento.FormatoArquivo.PDF,
            arquivo_original="documentos/boleto.pdf",
            origem="upload_manual",
            criado_por=usuario,
        )
        lancamento = LancamentoPreparado.objects.create(
            documento=doc,
            origem="upload_manual",
            data="2026-07-20",
            dados_finais={"valor": "1000.00"},
            criado_por=usuario,
        )
        assert lancamento.documento is not None
        assert lancamento.origem == "upload_manual"
        assert lancamento.data is not None

    def test_lancamento_requires_documento(self, usuario):
        """LancamentoPreparado must have a document reference."""
        with pytest.raises(IntegrityError):
            LancamentoPreparado.objects.create(
                documento=None,
                origem="upload_manual",
                data="2026-07-20",
                dados_finais={},
            )

    def test_lancamento_requires_origem(self, usuario):
        """LancamentoPreparado must have an origin."""
        doc = Documento.objects.create(
            tipo_documento=Documento.TipoDocumento.NOTA_FISCAL,
            formato_arquivo=Documento.FormatoArquivo.PDF,
            arquivo_original="documentos/nf.pdf",
            origem="upload_manual",
            criado_por=usuario,
        )
        with pytest.raises(IntegrityError):
            LancamentoPreparado.objects.create(
                documento=doc,
                origem=None,
                data="2026-07-20",
                dados_finais={},
            )


@pytest.mark.django_db
class TestDadosExtraidos:
    """Tests for DadosExtraidos model."""

    def test_create_dados_extraidos(self, usuario):
        doc = Documento.objects.create(
            tipo_documento=Documento.TipoDocumento.NOTA_FISCAL,
            formato_arquivo=Documento.FormatoArquivo.PDF,
            arquivo_original="documentos/nf.pdf",
            origem="upload_manual",
            criado_por=usuario,
        )
        dados = DadosExtraidos.objects.create(
            documento=doc,
            campos_extraidos={"numero": "12345", "valor_total": "1500.00"},
            provedor_llm_utilizado="ollama",
            modelo_llm_utilizado="llama3",
            tentativas_realizadas=1,
            precisa_revisao=False,
        )
        assert dados.documento == doc
        assert dados.campos_extraidos["numero"] == "12345"
        assert dados.precisa_revisao is False
