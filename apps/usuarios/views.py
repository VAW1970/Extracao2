"""Views for the usuarios app."""

from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class UsuarioLoginView(auth_views.LoginView):
    """Custom login view."""

    template_name = "usuarios/login.html"
    redirect_authenticated_user = True


class UsuarioLogoutView(auth_views.LogoutView):
    """Custom logout view."""

    next_page = "/usuarios/login/"


class PerfilView(LoginRequiredMixin, TemplateView):
    """User profile view."""

    template_name = "usuarios/perfil.html"
