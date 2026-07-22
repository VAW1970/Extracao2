"""
Django application configuration for the extracao_contabil project.
"""

from django.apps import AppConfig


class ExtracaoConfig(AppConfig):
    """Main application configuration."""

    default = True
    name = "config"
    verbose_name = "Extração Contábil"

    def ready(self):
        """Configure admin site branding after Django is fully loaded."""
        from django.contrib import admin

        admin.site.site_header = "Administração — Extração Contábil"
        admin.site.index_title = "Painel de Controle"
        admin.site.site_title = "Admin — Extração Contábil"