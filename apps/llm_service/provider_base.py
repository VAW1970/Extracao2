"""
LLM Provider Base Interface.

All LLM providers must implement this abstract base class.
The system never depends on provider-specific details — all communication
goes through this common interface.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("apps.llm_service")


class LLMProviderBase(ABC):
    """Abstract base class for LLM providers.

    All concrete providers (Ollama, API) must implement the `extrair` method.
    The method receives document content and a prompt template, and returns
    structured data as a dictionary.
    """

    @abstractmethod
    def extrair(
        self,
        conteudo_documento: str | bytes,
        prompt_template: str,
        schema_esperado: dict,
        is_multimodal: bool = False,
    ) -> dict[str, Any]:
        """Extract structured data from a document using the LLM.

        Args:
            conteudo_documento: The document content (text for text-based docs,
                bytes/base64 for images/multimodal).
            prompt_template: The prompt template for this document type.
            schema_esperado: The expected JSON schema for validation.
            is_multimodal: Whether the input includes image data.

        Returns:
            A dictionary with the extracted fields.

        Raises:
            LLMExtractionError: If the LLM call fails or returns invalid data.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider identifier (e.g., 'ollama', 'api')."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used."""
        pass


class LLMExtractionError(Exception):
    """Raised when LLM extraction fails."""

    pass
