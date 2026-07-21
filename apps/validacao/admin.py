from django.contrib import admin

from .models import LancamentoPreparado, ValidacaoLog


@admin.register(ValidacaoLog)
class ValidacaoLogAdmin(admin.ModelAdmin):
    list_display = ("id", "documento", "usuario_validador", "decisao", "data_validacao")
    list_filter = ("decisao",)
    readonly_fields = ("data_validacao",)


@admin.register(LancamentoPreparado)
class LancamentoPreparadoAdmin(admin.ModelAdmin):
    list_display = ("id", "documento", "origem", "data", "status_exportacao", "data_criacao")
    list_filter = ("status_exportacao",)
    readonly_fields = ("data_criacao",)
