"""
Models for the documentos app.

Documento: represents an uploaded document (PDF, image, XML).
DadosExtraidos: stores extracted data from LLM processing.
"""

from django.db import models

from .storage import get_upload_path


class Documento(models.Model):
    """Represents an uploaded accounting/fiscal document."""

    class TipoDocumento(models.TextChoices):
        NOTA_FISCAL = "nota_fiscal", "Nota Fiscal"
        CONTRATO = "contrato", "Contrato"
        DEMONSTRATIVO = "demonstrativo", "Demonstrativo"
        BOLETO = "boleto", "Boleto"

    class FormatoArquivo(models.TextChoices):
        PDF = "pdf", "PDF"
        IMAGEM = "imagem", "Imagem (JPG/PNG)"
        XML = "xml", "XML"

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        VALIDADO = "validado", "Validado"
        REJEITADO = "rejeitado", "Rejeitado"

    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
        verbose_name="Tipo de Documento",
    )
    formato_arquivo = models.CharField(
        max_length=10,
        choices=FormatoArquivo.choices,
        verbose_name="Formato do Arquivo",
    )
    arquivo_original = models.FileField(
        upload_to=get_upload_path,
        verbose_name="Arquivo Original",
    )
    origem = models.CharField(
        max_length=50,
        default="upload_manual",
        verbose_name="Origem",
        help_text="Ex: upload_manual, e-mail, api",
    )
    data_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data do Upload",
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDENTE,
        verbose_name="Status",
    )
    criado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos",
        verbose_name="Criado por",
    )

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        db_table = "documentos"
        ordering = ["-data_upload"]

    def __str__(self) -> str:
        return f"{self.get_tipo_documento_display()} — {self.arquivo_original.name}"


class DadosExtraidos(models.Model):
    """Stores data extracted by the LLM from a document."""

    class ProvedorLLM(models.TextChoices):
        OLLAMA = "ollama", "Ollama (Local)"
        API = "api", "API Externa"

    documento = models.OneToOneField(
        Documento,
        on_delete=models.CASCADE,
        related_name="dados_extraidos",
        verbose_name="Documento",
    )
    campos_extraidos = models.JSONField(
        default=dict,
        verbose_name="Campos Extraídos",
    )
    provedor_llm_utilizado = models.CharField(
        max_length=10,
        choices=ProvedorLLM.choices,
        verbose_name="Provedor LLM Utilizado",
    )
    modelo_llm_utilizado = models.CharField(
        max_length=100,
        verbose_name="Modelo LLM Utilizado",
    )
    tempo_resposta_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Tempo de Resposta (ms)",
    )
    tokens_utilizados = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Tokens Utilizados",
    )
    tentativas_realizadas = models.IntegerField(
        default=1,
        verbose_name="Tentativas Realizadas",
    )
    precisa_revisao = models.BooleanField(
        default=False,
        verbose_name="Precisa Revisão",
    )
    resposta_bruta_llm = models.TextField(
        null=True,
        blank=True,
        verbose_name="Resposta Bruta do LLM",
        help_text="Armazenada apenas em caso de falha de validação.",
    )
    data_extracao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Extração",
    )

    class Meta:
        verbose_name = "Dados Extraídos"
        verbose_name_plural = "Dados Extraídos"
        db_table = "dados_extraidos"

    def __str__(self) -> str:
        return f"Dados de {self.documento}"
