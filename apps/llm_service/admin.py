from django.contrib import admin

from .models import LLMConfig


@admin.register(LLMConfig)
class LLMConfigAdmin(admin.ModelAdmin):
    list_display = ("provider", "active_model", "is_configured", "updated_at")
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        """Only one config instance should exist."""
        return not LLMConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Config should never be deleted."""
        return False
