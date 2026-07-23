from django.contrib import admin

from .models import Documento, DadosExtraidos


class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tipo_documento",
        "formato_arquivo",
        "status",
        "origem",
        "criado_por",
        "data_upload",
    )
    list_display_links = ("id", "tipo_documento")
    list_filter = ("tipo_documento", "formato_arquivo", "status")
    search_fields = ("tipo_documento", "origem", "arquivo_original")
    readonly_fields = ("data_upload",)
    date_hierarchy = "data_upload"
    ordering = ("-data_upload",)


class DadosExtraidosAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "documento",
        "provedor_llm_utilizado",
        "modelo_llm_utilizado",
        "tentativas_realizadas",
        "precisa_revisao",
        "tempo_resposta_ms",
        "data_extracao",
    )
    list_display_links = ("id", "documento")
    list_filter = ("provedor_llm_utilizado", "precisa_revisao")
    search_fields = ("documento__arquivo_original", "modelo_llm_utilizado")
    readonly_fields = ("data_extracao",)
    date_hierarchy = "data_extracao"
    ordering = ("-data_extracao",)

    def has_add_permission(self, request):
        return False
