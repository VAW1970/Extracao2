"""
Models for the validacao app.

ValidacaoLog: audit log of human validation actions.
LancamentoPreparado: final prepared entry ready for accounting export.
"""

from django.db import models


class ValidacaoLog(models.Model):
    """Audit log for human validation of extracted data."""

    class Decisao(models.TextChoices):
        APROVADO = "aprovado", "Aprovado"
        REJEITADO = "rejeitado", "Rejeitado"

    documento = models.ForeignKey(
        "documentos.Documento",
        on_delete=models.CASCADE,
        related_name="validacoes",
        verbose_name="Documento",
    )
    usuario_validador = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="validacoes_realizadas",
        verbose_name="Usuário Validador",
    )
    data_validacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Validação",
    )
    alteracoes_realizadas = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Alterações Realizadas",
        help_text="Dicionário com os campos alterados manualmente.",
    )
    decisao = models.CharField(
        max_length=10,
        choices=Decisao.choices,
        verbose_name="Decisão",
    )

    class Meta:
        verbose_name = "Log de Validação"
        verbose_name_plural = "Logs de Validação"
        db_table = "validacao_log"
        ordering = ["-data_validacao"]

    def __str__(self) -> str:
        return f"{self.get_decisao_display()} — Doc {self.documento.id} por {self.usuario_validador}"


class LancamentoPreparado(models.Model):
    """A prepared accounting entry, ready for export to external system.

    CRITICAL CONSTRAINTS:
    - documento: null=False (MUST reference a document)
    - origem: null=False (MUST have an origin)
    - data: null=False (MUST have a date)
    """

    class StatusExportacao(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EXPORTADO = "exportado", "Exportado"

    documento = models.ForeignKey(
        "documentos.Documento",
        on_delete=models.PROTECT,
        related_name="lancamentos_preparados",
        verbose_name="Documento",
        null=False,
    )
    origem = models.CharField(
        max_length=50,
        verbose_name="Origem",
        null=False,
        help_text="Ex: upload_manual, e-mail, api",
    )
    data = models.DateField(
        verbose_name="Data do Lançamento",
        null=False,
    )
    dados_finais = models.JSONField(
        default=dict,
        verbose_name="Dados Finais",
        help_text="Dados validados pelo usuário, prontos para lançamento.",
    )
    status_exportacao = models.CharField(
        max_length=15,
        choices=StatusExportacao.choices,
        default=StatusExportacao.PENDENTE,
        verbose_name="Status de Exportação",
    )
    criado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos_preparados",
        verbose_name="Criado por",
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação",
    )

    class Meta:
        verbose_name = "Lançamento Preparado"
        verbose_name_plural = "Lançamentos Preparados"
        db_table = "lancamentos_preparados"
        ordering = ["-data_criacao"]

    def __str__(self) -> str:
        return f"Lançamento {self.id} — Doc {self.documento.id} ({self.data})"
