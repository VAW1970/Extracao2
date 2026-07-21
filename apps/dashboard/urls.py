"""URL configuration for dashboard app."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="index"),
    path("exportar-csv/", views.ExportCSVView.as_view(), name="export_csv"),
]
