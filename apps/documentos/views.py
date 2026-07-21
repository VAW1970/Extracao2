"""Views for the documentos app."""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView

from .forms import DocumentoUploadForm
from .models import Documento, DadosExtraidos

logger = logging.getLogger("apps.documentos")


class DocumentoListView(LoginRequiredMixin, ListView):
    """List all documents uploaded by the current user."""

    model = Documento
    template_name = "documentos/list.html"
    context_object_name = "documentos"
    paginate_by = 20

    def get_queryset(self):
        return Documento.objects.filter(criado_por=self.request.user)


class DocumentoUploadView(LoginRequiredMixin, CreateView):
    """Upload a new document for extraction."""

    model = Documento
    form_class = DocumentoUploadForm
    template_name = "documentos/upload.html"
    def form_valid(self, form: DocumentoUploadForm) -> HttpResponse:
        """Process valid form: determine format, save document, and trigger extraction."""
        documento = form.save(commit=False)
        documento.criado_por = self.request.user

        # Determine file format from filename
        arquivo = form.cleaned_data["arquivo_original"]
        documento.formato_arquivo = form.determine_formato(arquivo)

        documento.save()
        logger.info(f"Documento {documento.id} uploaded by {self.request.user}")

        # Trigger LLM extraction synchronously (serverless environment)
        from apps.llm_service.services import extrair_dados
        try:
            dados = extrair_dados(documento.id)
            if dados and not dados.precisa_revisao:
                messages.success(
                    self.request,
                    f"Documento '{arquivo.name}' enviado e extraído com sucesso!",
                )
            elif dados:
                messages.warning(
                    self.request,
                    f"Documento '{arquivo.name}' enviado. Extração precisa de revisão.",
                )
            else:
                messages.warning(
                    self.request,
                    f"Documento '{arquivo.name}' enviado. Extração falhou — use 'Extrair' nos detalhes.",
                )
        except Exception as e:
            logger.warning(f"Extraction failed for document {documento.id}: {e}")
            messages.warning(
                self.request,
                f"Documento '{arquivo.name}' enviado. Clique em 'Extrair' para processar.",
            )

        return redirect("documentos:detail", pk=documento.id)


class DocumentoDetailView(LoginRequiredMixin, DetailView):
    """View document details and extracted data."""

    model = Documento
    template_name = "documentos/detail.html"
    context_object_name = "documento"


class DocumentoExtrairView(LoginRequiredMixin, View):
    """Manually trigger LLM extraction for a document."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        documento = get_object_or_404(Documento, pk=pk)

        if documento.status == Documento.Status.VALIDADO:
            messages.warning(request, "Documento já validado. Não é possível reprocessar.")
            return redirect("documentos:detail", pk=pk)

        from apps.llm_service.services import extrair_dados

        # Delete existing extracted data before reprocessing (OneToOneField constraint)
        DadosExtraidos.objects.filter(documento=documento).delete()

        try:
            dados = extrair_dados(documento.id)
            if dados and not dados.precisa_revisao:
                messages.success(request, f"Documento {documento.id} extraído com sucesso!")
            elif dados:
                messages.warning(request, f"Documento {documento.id} extraído, mas precisa de revisão.")
            else:
                messages.warning(request, f"Documento {documento.id}: extração falhou. Verifique os logs.")
        except Exception as e:
            logger.error(f"Extraction error for document {documento.id}: {e}")
            messages.error(request, f"Erro na extração: {str(e)[:200]}")

        return redirect("documentos:detail", pk=pk)


class DocumentoDeleteView(LoginRequiredMixin, DeleteView):
    """Soft delete a document (mark as rejected, don't delete from storage)."""

    model = Documento
    template_name = "documentos/delete_confirm.html"
    success_url = "/documentos/"

    def form_valid(self, form):
        """Mark document as rejected instead of actually deleting."""
        documento = self.get_object()
        documento.status = Documento.Status.REJEITADO
        documento.save()
        messages.info(self.request, f"Documento {documento.id} removido.")
        return redirect(self.success_url)
