"""
External API LLM Provider — Google Gemini (OpenAI-compatible endpoint).

Uses Gemini for both text extraction (gemini-1.5-flash) and multimodal
extraction (gemini-1.5-flash) — same model handles text and images.
Configurable via LLM_API_KEY, LLM_MODEL, LLM_BASE_URL env variables.

Gemini provides an OpenAI-compatible endpoint:
    https://generativelanguage.googleapis.com/v1beta/openai/
"""

import base64
import json
import logging
import time
from typing import Any

from .provider_base import LLMExtractionError, LLMProviderBase

logger = logging.getLogger("apps.llm_service")

# Gemini OpenAI-compatible endpoint
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
GEMINI_DEFAULT_MODEL = "gemini-1.5-flash"


class APIProvider(LLMProviderBase):
    """LLM provider using Google Gemini API (OpenAI-compatible endpoint).

    Gemini supports both text and vision (images) in the same model,
    so there is no need for a separate vision provider.
    """

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self.api_key = api_key
        self.model = model or GEMINI_DEFAULT_MODEL
        self.base_url = (base_url or GEMINI_BASE_URL).rstrip("/")

    def get_provider_name(self) -> str:
        return "gemini"

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

        # Gemini supports both text and vision in the same model.
        # Use response_format=json_object only for text (Gemini may not
        # support it for multimodal responses).
        response_format = (
            {"type": "json_object"} if not is_multimodal else None
        )

        payload = {
            "model": self.model,
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

            # Parse the response — Gemini may wrap JSON in markdown, strip it
            content = result["choices"][0]["message"]["content"]
            # Remove markdown code fences if present
            if content.startswith("```"):
                content = content.split("```", 2)
                content = content[1] if len(content) > 1 else content[0]
                # Remove optional "json" language tag
                if content.lower().startswith("json"):
                    content = content[4:].strip()
            extracted = json.loads(content)

            # Add metadata
            usage = result.get("usage", {})
            extracted["_metadata"] = {
                "provider": "gemini",
                "model": self.model,
                "tempo_resposta_ms": elapsed_ms,
                "tokens_utilizados": usage.get("total_tokens"),
            }

            logger.info(
                f"Gemini extraction completed in {elapsed_ms}ms "
                f"using model {self.model}"
            )
            return extracted

        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini HTTP error: {e.response.status_code} — {e.response.text}")
            raise LLMExtractionError(f"Gemini returned error: {e.response.status_code}") from e
        except httpx.ConnectError:
            logger.error("Cannot connect to Gemini API")
            raise LLMExtractionError("Cannot connect to Gemini API. Check network and API key.")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise LLMExtractionError("Invalid response from Gemini API") from e

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
