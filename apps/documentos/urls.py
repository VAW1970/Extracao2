"""URL configuration for documentos app."""

from django.urls import path

from . import views

app_name = "documentos"

urlpatterns = [
    path("", views.DocumentoListView.as_view(), name="list"),
    path("upload/", views.DocumentoUploadView.as_view(), name="upload"),
    path("<int:pk>/", views.DocumentoDetailView.as_view(), name="detail"),
    path("<int:pk>/extrair/", views.DocumentoExtrairView.as_view(), name="extract"),
    path("<int:pk>/excluir/", views.DocumentoDeleteView.as_view(), name="delete"),
]
