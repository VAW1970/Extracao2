from django.apps import AppConfig


class LlmServiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.llm_service"
    verbose_name = "Serviço LLM"
