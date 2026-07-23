"""
Custom Admin Site configuration.

This module defines a custom AdminSite with project branding
and registers all models with it.
"""

from django.contrib.admin import AdminSite


class CustomAdminSite(AdminSite):
    """Custom admin site with project branding."""

    site_header = "Administração — Extração Contábil"
    site_title = "Admin — Extração Contábil"
    index_title = "Painel de Controle"

    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all installed apps with their models.

        Custom ordering:
        1. Usuários (usuarios)
        2. Documentos (documentos)
        3. Validação (validacao)
        4. LLM (llm_service)
        5. Sistema (auth)
        """
        app_dict = self._build_app_dict(request, app_label)

        # Custom order for apps
        app_order = {
            "usuarios": 1,
            "documentos": 2,
            "validacao": 3,
            "llm_service": 4,
            "auth": 5,
        }

        # Custom order for models within each app
        model_order = {
            "Usuario": 1,
            "Group": 2,
            "Documento": 1,
            "DadosExtraidos": 2,
            "ValidacaoLog": 1,
            "LancamentoPreparado": 2,
            "LLMConfig": 1,
        }

        # Sort apps
        apps = list(app_dict.values())
        apps.sort(key=lambda x: app_order.get(x["app_label"], 99))

        # Sort models within each app
        for app in apps:
            app["models"].sort(key=lambda x: model_order.get(x["object_name"], 99))

        return apps


# Create the custom admin site instance
admin_site = CustomAdminSite(name="admin")

# Import and register all models
from django.contrib.auth.models import Group
from apps.usuarios.models import Usuario
from apps.documentos.models import Documento, DadosExtraidos
from apps.validacao.models import LancamentoPreparado, ValidacaoLog
from apps.llm_service.models import LLMConfig
from apps.usuarios.admin import UsuarioAdmin
from apps.documentos.admin import DocumentoAdmin, DadosExtraidosAdmin
from apps.validacao.admin import LancamentoPreparadoAdmin, ValidacaoLogAdmin
from apps.llm_service.admin import LLMConfigAdmin

# Register models with custom admin site
admin_site.register(Usuario, UsuarioAdmin)
admin_site.register(Documento, DocumentoAdmin)
admin_site.register(DadosExtraidos, DadosExtraidosAdmin)
admin_site.register(ValidacaoLog, ValidacaoLogAdmin)
admin_site.register(LancamentoPreparado, LancamentoPreparadoAdmin)
admin_site.register(LLMConfig, LLMConfigAdmin)
admin_site.register(Group)