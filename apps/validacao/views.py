"""Views for the validacao app."""

import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.documentos.models import Documento, DadosExtraidos
from apps.usuarios.models import Usuario

from .models import LancamentoPreparado, ValidacaoLog

logger = logging.getLogger("apps.validacao")


class ValidacaoQueueView(LoginRequiredMixin, ListView):
    """Display the queue of documents pending validation."""

    model = Documento
    template_name = "validacao/queue.html"
    context_object_name = "documentos"
    paginate_by = 20

    def get_queryset(self):
        """Return documents with extracted data pending validation."""
        return (
            Documento.objects.filter(
                status=Documento.Status.PENDENTE,
                dados_extraidos__isnull=False,
            )
            .select_related("dados_extraidos")
            .order_by(
                "-dados_extraidos__precisa_revisao",  # Prioritize needing review
                "-data_upload",
            )
        )


class ValidacaoDetailView(LoginRequiredMixin, TemplateView):
    """Side-by-side validation view: original document + extracted data."""

    template_name = "validacao/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc_id = self.kwargs.get("pk")
        documento = get_object_or_404(
            Documento.objects.select_related("dados_extraidos"),
            pk=doc_id,
        )
        context["documento"] = documento

        # Get extracted data
        try:
            dados = DadosExtraidos.objects.get(documento=documento)
            context["dados_extraidos"] = dados
            context["campos_json"] = json.dumps(dados.campos_extraidos, indent=2, ensure_ascii=False)
        except DadosExtraidos.DoesNotExist:
            context["dados_extraidos"] = None
            context["campos_json"] = "{}"

        return context


class ValidacaoAprovarView(LoginRequiredMixin, View):
    """Approve extracted data and create LancamentoPreparado."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        documento = get_object_or_404(Documento, pk=pk)

        # Get the edited data from form submission
        campos_editados = {}
        for key, value in request.POST.items():
            if key.startswith("campo_"):
                campo_nome = key.replace("campo_", "")
                campos_editados[campo_nome] = value

        # If no edits, use original extracted data
        if not campos_editados:
            try:
                dados = DadosExtraidos.objects.get(documento=documento)
                campos_editados = dados.campos_extraidos
            except DadosExtraidos.DoesNotExist:
                messages.error(request, "Dados extraídos não encontrados.")
                return redirect("validacao:queue")

        # Create LancamentoPreparado
        from django.utils import timezone

        lancamento = LancamentoPreparado.objects.create(
            documento=documento,
            origem=documento.origem,
            data=timezone.now().date(),
            dados_finais=campos_editados,
            criado_por=request.user,
        )

        # Update document status
        documento.status = Documento.Status.VALIDADO
        documento.save()

        # Log the validation
        ValidacaoLog.objects.create(
            documento=documento,
            usuario_validador=request.user,
            decisao=ValidacaoLog.Decisao.APROVADO,
            alteracoes_realizadas=campos_editados,
        )

        logger.info(f"Documento {documento.id} aprovado por {request.user}")
        messages.success(request, f"Documento {documento.id} aprovado! Lançamento preparado #{lancamento.id} criado.")

        return redirect("validacao:queue")


class ValidacaoRejeitarView(LoginRequiredMixin, View):
    """Reject extracted data."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        documento = get_object_or_404(Documento, pk=pk)

        # Log the rejection
        ValidacaoLog.objects.create(
            documento=documento,
            usuario_validador=request.user,
            decisao=ValidacaoLog.Decisao.REJEITADO,
            alteracoes_realizadas={"motivo": request.POST.get("motivo", "")},
        )

        # Update document status
        documento.status = Documento.Status.REJEITADO
        documento.save()

        logger.info(f"Documento {documento.id} rejeitado por {request.user}")
        messages.warning(request, f"Documento {documento.id} rejeitado.")

        return redirect("validacao:queue")
