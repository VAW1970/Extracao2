"""
External API LLM Provider.

Mandatory in production (Vercel). Supports multimodal models via OpenAI-compatible API.
Configurable via LLM_API_KEY and LLM_MODEL environment variables.
"""

import base64
import json
import logging
import time
from typing import Any

from .provider_base import LLMExtractionError, LLMProviderBase

logger = logging.getLogger("apps.llm_service")


class APIProvider(LLMProviderBase):
    """LLM provider using an external API (OpenAI, Anthropic, etc.).

    This provider is mandatory in production on Vercel since Ollama
    cannot run in a serverless environment.
    """

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self.api_key = api_key
        self.model = model
        self.default_model = model  # for text documents
        self.vision_model = "meta-llama/llama-4-scout-17b-16e-instruct"  # for images
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")

    def get_provider_name(self) -> str:
        return "api"

    def get_model_name(self) -> str:
        return self.model

    def extrair(
        self,
        conteudo_documento: str | bytes,
        prompt_template: str,
        schema_esperado: dict,
        is_multimodal: bool = False,
    ) -> dict[str, Any]:
        """Extract data using an external LLM API (OpenAI-compatible)."""
        import httpx

        start_time = time.time()

        # Build messages
        messages = self._build_messages(
            conteudo_documento, prompt_template, is_multimodal
        )

        # Use vision model for multimodal content (images)
        active_model = self.vision_model if is_multimodal else self.default_model
        # Vision models may not support json_object response_format
        response_format = (
            None if is_multimodal else {"type": "json_object"}
        )

        payload = {
            "model": active_model,
            "messages": messages,
            "temperature": 0.1,
        }
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

            result = response.json()
            elapsed_ms = int((time.time() - start_time) * 1000)

            # Parse the response
            content = result["choices"][0]["message"]["content"]
            extracted = json.loads(content)

            # Add metadata
            usage = result.get("usage", {})
            extracted["_metadata"] = {
                "provider": "api",
                "model": active_model,
                "tempo_resposta_ms": elapsed_ms,
                "tokens_utilizados": usage.get("total_tokens"),
            }

            logger.info(
                f"API extraction completed in {elapsed_ms}ms "
                f"using model {active_model}"
            )
            return extracted

        except httpx.HTTPStatusError as e:
            logger.error(f"API HTTP error: {e.response.status_code} — {e.response.text}")
            raise LLMExtractionError(f"API returned error: {e.response.status_code}") from e
        except httpx.ConnectError:
            logger.error("Cannot connect to LLM API")
            raise LLMExtractionError("Cannot connect to LLM API. Check network and API key.")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse API response: {e}")
            raise LLMExtractionError("Invalid response from LLM API") from e

    def _build_messages(
        self,
        conteudo_documento: str | bytes,
        prompt_template: str,
        is_multimodal: bool,
    ) -> list[dict]:
        """Build messages for the OpenAI-compatible chat API."""
        if is_multimodal and isinstance(conteudo_documento, bytes):
            image_b64 = base64.b64encode(conteudo_documento).decode("utf-8")
            # Detect image format by magic bytes
            if conteudo_documento[:8] == b"\x89PNG\r\n\x1a\n":
                image_mime = "image/png"
            elif conteudo_documento[:3] == b"\xff\xd8\xff":
                image_mime = "image/jpeg"
            else:
                image_mime = "image/jpeg"
            return [
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em extração de dados de documentos contábeis brasileiros. Responda APENAS com JSON válido, sem texto adicional, sem markdown.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_template},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_mime};base64,{image_b64}",
                            },
                        },
                    ],
                },
            ]
        else:
            full_prompt = f"{prompt_template}\n\n---\nConteúdo do documento:\n{conteudo_documento}"
            return [
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em extração de dados de documentos contábeis brasileiros. Responda APENAS com JSON válido, sem texto adicional, sem markdown.",
                },
                {
                    "role": "user",
                    "content": full_prompt,
                },
            ]
