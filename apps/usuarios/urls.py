"""URL configuration for usuarios app."""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("login/", views.UsuarioLoginView.as_view(), name="login"),
    path("logout/", views.UsuarioLogoutView.as_view(), name="logout"),
    path("perfil/", views.PerfilView.as_view(), name="perfil"),
]
