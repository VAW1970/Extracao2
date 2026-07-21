"""
Ollama LLM Provider.

Usage restricted to local development environment only.
Configurable via OLLAMA_HOST and OLLAMA_MODEL environment variables.
Supports multimodal models (e.g., llava) for image-based documents.
"""

import base64
import json
import logging
import time
from typing import Any

from .provider_base import LLMExtractionError, LLMProviderBase

logger = logging.getLogger("apps.llm_service")


class OllamaProvider(LLMProviderBase):
    """LLM provider using Ollama for local development.

    Ollama runs models locally and is NOT viable in production on Vercel
    because it requires a persistent process with the model loaded in memory.
    """

    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def get_provider_name(self) -> str:
        return "ollama"

    def get_model_name(self) -> str:
        return self.model

    def extrair(
        self,
        conteudo_documento: str | bytes,
        prompt_template: str,
        schema_esperado: dict,
        is_multimodal: bool = False,
    ) -> dict[str, Any]:
        """Extract data using Ollama API."""
        import httpx

        start_time = time.time()

        # Build the messages payload
        messages = self._build_messages(
            conteudo_documento, prompt_template, is_multimodal
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "format": "json",
            "stream": False,
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.host}/api/chat",
                    json=payload,
                )
                response.raise_for_status()

            result = response.json()
            elapsed_ms = int((time.time() - start_time) * 1000)

            # Parse the response content
            content = result.get("message", {}).get("content", "")
            extracted = self._parse_response(content)

            # Add metadata
            extracted["_metadata"] = {
                "provider": "ollama",
                "model": self.model,
                "tempo_resposta_ms": elapsed_ms,
                "tokens_utilizados": result.get("eval_count"),
            }

            logger.info(
                f"Ollama extraction completed in {elapsed_ms}ms "
                f"using model {self.model}"
            )
            return extracted

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code} — {e.response.text}")
            raise LLMExtractionError(f"Ollama returned error: {e.response.status_code}") from e
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.host}")
            raise LLMExtractionError(
                f"Cannot connect to Ollama at {self.host}. "
                "Ensure Ollama is running locally."
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response as JSON: {e}")
            raise LLMExtractionError("Invalid JSON in LLM response") from e

    def _build_messages(
        self,
        conteudo_documento: str | bytes,
        prompt_template: str,
        is_multimodal: bool,
    ) -> list[dict]:
        """Build the messages array for the Ollama chat API."""
        if is_multimodal and isinstance(conteudo_documento, bytes):
            # Multimodal: encode image as base64
            image_b64 = base64.b64encode(conteudo_documento).decode("utf-8")
            return [
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em extração de dados de documentos contábeis. Responda APENAS com JSON válido.",
                },
                {
                    "role": "user",
                    "content": prompt_template,
                    "images": [image_b64],
                },
            ]
        else:
            # Text-based document
            full_prompt = f"{prompt_template}\n\n---\nConteúdo do documento:\n{conteudo_documento}"
            return [
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em extração de dados de documentos contábeis. Responda APENAS com JSON válido.",
                },
                {
                    "role": "user",
                    "content": full_prompt,
                },
            ]

    def _parse_response(self, content: str) -> dict:
        """Parse the LLM response, stripping markdown and extracting JSON."""
        # Remove markdown code fences if present
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        return json.loads(cleaned)
