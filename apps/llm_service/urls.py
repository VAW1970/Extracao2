"""URL configuration for llm_service app."""

from django.urls import path

from . import views

app_name = "llm_service"

urlpatterns = [
    path("config/", views.LLMConfigView.as_view(), name="config"),
    path("test-connection/", views.LLMTestConnectionView.as_view(), name="test_connection"),
]
