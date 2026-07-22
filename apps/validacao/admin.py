from django.contrib import admin

from .models import LancamentoPreparado, ValidacaoLog


@admin.register(ValidacaoLog)
class ValidacaoLogAdmin(admin.ModelAdmin):
    list_display = ("id", "documento", "usuario_validador", "decisao", "data_validacao")
    list_display_links = ("id", "documento")
    list_filter = ("decisao",)
    search_fields = ("documento__arquivo_original", "usuario_validador__username")
    readonly_fields = ("data_validacao",)
    date_hierarchy = "data_validacao"
    ordering = ("-data_validacao",)


@admin.register(LancamentoPreparado)
class LancamentoPreparadoAdmin(admin.ModelAdmin):
    list_display = ("id", "documento", "origem", "data", "status_exportacao", "data_criacao")
    list_display_links = ("id", "documento")
    list_filter = ("status_exportacao",)
    search_fields = ("documento__arquivo_original", "origem")
    readonly_fields = ("data_criacao",)
    date_hierarchy = "data_criacao"
    ordering = ("-data_criacao",)
