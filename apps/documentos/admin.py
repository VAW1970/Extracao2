from django.contrib import admin

from .models import Documento, DadosExtraidos


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo_documento", "formato_arquivo", "status", "origem", "data_upload")
    list_filter = ("tipo_documento", "formato_arquivo", "status")
    search_fields = ("tipo_documento", "origem")
    readonly_fields = ("data_upload",)


@admin.register(DadosExtraidos)
class DadosExtraidosAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "documento",
        "provedor_llm_utilizado",
        "modelo_llm_utilizado",
        "precisa_revisao",
        "data_extracao",
    )
    list_filter = ("provedor_llm_utilizado", "precisa_revisao")
    readonly_fields = ("data_extracao",)
