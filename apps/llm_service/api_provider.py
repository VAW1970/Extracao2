"""
External API LLM Provider — OpenAI-compatible endpoint (Groq, OpenAI, etc.).

Configurable via environment variables:
    LLM_API_KEY       - API key for the provider
    LLM_MODEL         - Text model (default: llama-3.3-70b-versatile for Groq)
    LLM_BASE_URL      - API base URL (default: https://api.groq.com/openai/v1 for Groq)
    VISION_LLM_MODEL  - Vision model for images (default: llama-3.2-90b-vision-preview for Groq)
    VISION_LLM_BASE_URL - Optional separate endpoint for vision
    VISION_LLM_API_KEY  - Optional separate API key for vision
"""

import base64
import json
import logging
import os
import time
from typing import Any

from .provider_base import LLMExtractionError, LLMProviderBase

logger = logging.getLogger("apps.llm_service")

# Groq defaults (OpenAI-compatible)
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"
GROQ_VISION_DEFAULT_MODEL = "llama-3.2-90b-vision-preview"


class APIProvider(LLMProviderBase):
    """LLM provider using an OpenAI-compatible API (Groq, OpenAI, etc.)."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self.api_key = api_key
        self.model = model or GROQ_DEFAULT_MODEL
        self.base_url = (base_url or GROQ_BASE_URL).rstrip("/")
        # Vision model for multimodal (images/scanned PDFs)
        self.vision_model = os.environ.get("VISION_LLM_MODEL", GROQ_VISION_DEFAULT_MODEL)
        self.vision_base_url = os.environ.get("VISION_LLM_BASE_URL", self.base_url).rstrip("/")
        self.vision_api_key = os.environ.get("VISION_LLM_API_KEY", self.api_key)

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
        """Extract data using an OpenAI-compatible API."""
        import httpx

        start_time = time.time()

        messages = self._build_messages(
            conteudo_documento, prompt_template, is_multimodal
        )

        # Select model and endpoint based on modality
        if is_multimodal:
            active_model = self.vision_model
            active_base_url = self.vision_base_url
            active_api_key = self.vision_api_key
        else:
            active_model = self.model
            active_base_url = self.base_url
            active_api_key = self.api_key

        payload = {
            "model": active_model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4096,
        }

        headers = {
            "Authorization": f"Bearer {active_api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{active_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

            result = response.json()
            elapsed_ms = int((time.time() - start_time) * 1000)

            content = result["choices"][0]["message"]["content"]
            extracted = self._parse_json_response(content)

            usage = result.get("usage", {})
            extracted["_metadata"] = {
                "provider": "api",
                "model": active_model,
                "tempo_resposta_ms": elapsed_ms,
                "tokens_utilizados": usage.get("total_tokens"),
            }

            logger.info(
                f"API extraction completed in {elapsed_ms}ms using model {active_model}"
            )
            return extracted

        except httpx.HTTPStatusError as e:
            logger.error(f"API HTTP error: {e.response.status_code} — {e.response.text}")
            raise LLMExtractionError(f"API returned error: {e.response.status_code}") from e
        except httpx.ConnectError:
            logger.error("Cannot connect to API")
            raise LLMExtractionError("Cannot connect to API. Check network and API key.")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse API response: {e}")
            raise LLMExtractionError("Invalid response from API") from e

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from LLM response, stripping markdown fences if present."""
        content = content.strip()

        if content.startswith("```"):
            parts = content.split("```")
            if len(parts) >= 3:
                content = parts[1].strip()
            if content.lower().startswith("json"):
                content = content[4:].strip()

        return json.loads(content)

    def _build_messages(
        self,
        conteudo_documento: str | bytes,
        prompt_template: str,
        is_multimodal: bool,
    ) -> list[dict]:
        """Build messages for OpenAI-compatible chat API."""
        system_msg = (
            "Você é um assistente especializado em extração de dados de "
            "documentos contábeis brasileiros. Responda APENAS com JSON "
            "válido, sem texto adicional, sem markdown."
        )

        if is_multimodal and isinstance(conteudo_documento, bytes):
            image_b64 = base64.b64encode(conteudo_documento).decode("utf-8")
            # Detect image format
            if conteudo_documento[:8] == b"\x89PNG\r\n\x1a\n":
                image_mime = "image/png"
            elif conteudo_documento[:3] == b"\xff\xd8\xff":
                image_mime = "image/jpeg"
            else:
                image_mime = "image/jpeg"

            return [
                {"role": "system", "content": system_msg},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_template},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_mime};base64,{image_b64}"
                            },
                        },
                    ],
                },
            ]
        else:
            full_prompt = f"{prompt_template}\n\n---\nConteúdo do documento:\n{conteudo_documento}"
            return [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": full_prompt},
            ]


# Import base64 at module level
import base64