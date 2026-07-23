from django.contrib import admin

from .models import LLMConfig


class LLMConfigAdmin(admin.ModelAdmin):
    list_display = ("provider", "active_model", "is_configured", "updated_at")
    list_display_links = ("provider", "active_model")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Provedor", {"fields": ("provider",)}),
        ("Ollama (desenvolvimento local)", {"fields": ("ollama_host", "ollama_model"), "classes": ("collapse",)}),
        ("API Externa (produção)", {"fields": ("api_provider_name", "api_base_url", "api_key", "api_model")}),
        ("Configurações gerais", {"fields": ("max_retries", "timeout_seconds")}),
        ("Metadados", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        return not LLMConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
