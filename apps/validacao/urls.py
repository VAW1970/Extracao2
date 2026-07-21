"""URL configuration for validacao app."""

from django.urls import path

from . import views

app_name = "validacao"

urlpatterns = [
    path("", views.ValidacaoQueueView.as_view(), name="queue"),
    path("<int:pk>/", views.ValidacaoDetailView.as_view(), name="detail"),
    path("<int:pk>/aprovar/", views.ValidacaoAprovarView.as_view(), name="approve"),
    path("<int:pk>/rejeitar/", views.ValidacaoRejeitarView.as_view(), name="reject"),
]
