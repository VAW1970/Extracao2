"""Views for the dashboard app."""

import csv
import io
import json
import logging
from datetime import timedelta

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, F, IntegerField, Q
from django.db.models.functions import Cast
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.documentos.models import Documento, DadosExtraidos
from apps.validacao.models import LancamentoPreparado

logger = logging.getLogger("apps.dashboard")


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard with controls, charts, and LLM usage panel."""

    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # ── Totals by status ──
        context["total_documentos"] = Documento.objects.count()
        context["pendentes"] = Documento.objects.filter(status=Documento.Status.PENDENTE).count()
        context["validados"] = Documento.objects.filter(status=Documento.Status.VALIDADO).count()
        context["rejeitados"] = Documento.objects.filter(status=Documento.Status.REJEITADO).count()

        # ── Totals by type ──
        tipo_qs = (
            Documento.objects.values("tipo_documento")
            .annotate(total=Count("id"))
            .order_by("tipo_documento")
        )
        context["por_tipo"] = list(tipo_qs)
        context["por_tipo_json"] = json.dumps(list(tipo_qs), default=str)

        # ── LLM Usage Panel ──
        llm_stats = DadosExtraidos.objects.aggregate(
            total_extracoes=Count("id"),
            taxa_precisa_revisao=Avg(
                Cast("precisa_revisao", output_field=IntegerField())
            ),
            tempo_medio_ms=Avg("tempo_resposta_ms"),
        )
        context["llm_stats"] = llm_stats

        # Most used provider/model
        provider_stats = (
            DadosExtraidos.objects.values("provedor_llm_utilizado", "modelo_llm_utilizado")
            .annotate(total=Count("id"))
            .order_by("-total")
            .first()
        )
        context["provedor_mais_utilizado"] = provider_stats

        # ── Lancamentos prepared ──
        context["total_lancamentos"] = LancamentoPreparado.objects.count()
        context["lancamentos_pendentes"] = LancamentoPreparado.objects.filter(
            status_exportacao=LancamentoPreparado.StatusExportacao.PENDENTE
        ).count()

        # ── Recent documents ──
        context["documentos_recentes"] = Documento.objects.select_related(
            "dados_extraidos"
        ).order_by("-data_upload")[:10]

        # ── Filters ──
        context["filtro_tipo"] = self.request.GET.get("tipo", "")
        context["filtro_status"] = self.request.GET.get("status", "")
        context["filtro_data_inicio"] = self.request.GET.get("data_inicio", "")
        context["filtro_data_fim"] = self.request.GET.get("data_fim", "")

        return context


class ExportCSVView(LoginRequiredMixin, TemplateView):
    """Export validated lancamentos as CSV."""

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = "attachment; filename='lancamentos_validados.csv'"

        # BOM for Excel compatibility
        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow([
            "ID Lançamento",
            "ID Documento",
            "Tipo Documento",
            "Origem",
            "Data Lançamento",
            "Dados Finais",
            "Status Exportação",
            "Data Criação",
        ])

        lancamentos = LancamentoPreparado.objects.select_related("documento").filter(
            status_exportacao=LancamentoPreparado.StatusExportacao.PENDENTE
        )

        for lanc in lancamentos:
            writer.writerow([
                lanc.id,
                lanc.documento.id,
                lanc.documento.get_tipo_documento_display(),
                lanc.origem,
                lanc.data,
                json.dumps(lanc.dados_finais, ensure_ascii=False),
                lanc.get_status_exportacao_display(),
                lanc.data_criacao,
            ])

        # Mark as exported
        lancamentos.update(status_exportacao=LancamentoPreparado.StatusExportacao.EXPORTADO)

        logger.info(f"CSV exportado por {request.user} — {lancamentos.count()} lançamentos")
        return response


class AjudaView(LoginRequiredMixin, TemplateView):
    """Help page with user-friendly documentation."""

    template_name = "dashboard/ajuda.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Ajuda e Documentação"
        return context


class HelpView(LoginRequiredMixin, TemplateView):
    """Help page with user-friendly documentation."""

    template_name = "dashboard/help.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Ajuda — Extração Contábil"
        return context
