"""
Provider Factory — selects the active LLM provider based on configuration.

The choice is defined by the LLM_PROVIDER environment variable:
- "ollama": local Ollama (development only)
- "api": external API (mandatory in production)

Ollama is BLOCKED outside of development environments.
"""

import logging
import os

from django.conf import settings

from .nvidia_provider import NVIDIAProvider
from .ollama_provider import OllamaProvider
from .provider_base import LLMProviderBase

logger = logging.getLogger("apps.llm_service")


class MockProvider(LLMProviderBase):
    """Mock LLM provider for use exclusively in tests.

    Returns a pre-defined response without making any network calls.
    """

    def __init__(self, mock_response: dict | None = None):
        self.mock_response = mock_response or {}

    def get_provider_name(self) -> str:
        return "mock"

    def get_model_name(self) -> str:
        return "mock-model"

    def extrair(
        self,
        conteudo_documento: str | bytes,
        prompt_template: str,
        schema_esperado: dict,
        is_multimodal: bool = False,
    ) -> dict:
        """Return the pre-configured mock response."""
        response = self.mock_response.copy()
        response["_metadata"] = {
            "provider": "mock",
            "model": "mock-model",
            "tempo_resposta_ms": 0,
            "tokens_utilizados": 0,
        }
        return response


def get_llm_provider(testing: bool = False) -> LLMProviderBase:
    """Factory function to get the appropriate LLM provider.

    Reads configuration from the LLMConfig model in the database.
    Falls back to environment variables if the database config is not available.

    Args:
        testing: If True, returns a MockProvider.

    Returns:
        An instance of LLMProviderBase.

    Raises:
        ValueError: If the configured provider is invalid.
        RuntimeError: If Ollama is configured in production.
    """
    if testing:
        logger.info("Using MockProvider for testing")
        return MockProvider()

    # Try to load config from database first, fallback to env vars.
    db_config = None
    provider_type = settings.LLM_PROVIDER

    try:
        from .models import LLMConfig
        db_config = LLMConfig.get_active()
        if db_config.is_configured:
            provider_type = db_config.provider
    except (ImportError, LookupError, Exception) as exc:
        logger.debug(f"Could not load LLMConfig from database, using env vars: {exc}")
        pass

    if provider_type == "ollama":
        # Block Ollama in production
        is_production = os.environ.get("VERCEL", False) or os.environ.get("ENVIRONMENT") == "production"
        if is_production:
            raise RuntimeError(
                "Ollama is NOT supported in production on Vercel. "
                "Set LLM_PROVIDER=api and configure LLM_API_KEY."
            )

        if db_config and db_config.is_configured:
            host = db_config.ollama_host
            model = db_config.ollama_model
        else:
            host = settings.OLLAMA_HOST
            model = settings.OLLAMA_MODEL

        logger.info(f"Using Ollama provider at {host}")
        return OllamaProvider(host=host, model=model)

    elif provider_type == "api":
        # Use DB config if available, otherwise env vars.
        if db_config and db_config.is_configured and db_config.api_key:
            api_key = db_config.api_key
            model = db_config.api_model
            base_url = db_config.api_base_url
        else:
            api_key = settings.LLM_API_KEY
            model = settings.LLM_MODEL
            base_url = settings.LLM_BASE_URL

        logger.info(f"Using NVIDIA provider with model {model} at {base_url}")
        provider = NVIDIAProvider(api_key=api_key, model=model, base_url=base_url)
        return provider

    else:
        raise ValueError(
            f"Invalid LLM_PROVIDER: '{provider_type}'. "
            "Must be 'ollama' or 'api'."
        )
