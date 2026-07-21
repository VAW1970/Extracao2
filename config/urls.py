"""
Root URL configuration for extracao_contabil project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import include, path


def views_dashboard_redirect(request):
    """Redirect root URL to dashboard."""
    return HttpResponseRedirect("/dashboard/")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("usuarios/", include("apps.usuarios.urls")),
    path("documentos/", include("apps.documentos.urls")),
    path("validacao/", include("apps.validacao.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("llm/", include("apps.llm_service.urls")),
    # Root redirects to dashboard (only the index)
    path("", views_dashboard_redirect),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
