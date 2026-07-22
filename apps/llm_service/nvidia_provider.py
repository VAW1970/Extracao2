"""
NVIDIA API LLM Provider — uses NVIDIA's OpenAI-compatible endpoint.

NVIDIA provides an OpenAI-compatible API at https://integrate.api.nvidia.com/v1
with various models including vision-capable models.

Configuration via environment variables:
    NVIDIA_API_KEY    - API key from https://build.nvidia.com
    NVIDIA_MODEL      - Text model (default: nvidia/nemotron-3-ultra)
    NVIDIA_BASE_URL   - API base URL (default: https://integrate.api.nvidia.com/v1)
    VISION_NVIDIA_MODEL - Vision model (default: meta/llama-3.2-90b-vision-instruct)
"""

import base64
import json
import logging
import os
import time
from typing import Any

from .provider_base import LLMExtractionError, LLMProviderBase

logger = logging.getLogger("apps.llm_service")

# NVIDIA API defaults
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_DEFAULT_MODEL = "nvidia/nemotron-3-ultra"
NVIDIA_VISION_DEFAULT_MODEL = "meta/llama-3.2-90b-vision-instruct"


class NVIDIAProvider(LLMProviderBase):
    """LLM provider using NVIDIA's OpenAI-compatible API."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self.api_key = api_key
        self.model = model or NVIDIA_DEFAULT_MODEL
        self.base_url = (base_url or NVIDIA_BASE_URL).rstrip("/")
        # Vision model for multimodal (images/scanned PDFs)
        self.vision_model = os.environ.get("VISION_NVIDIA_MODEL", NVIDIA_VISION_DEFAULT_MODEL)

    def get_provider_name(self) -> str:
        return "nvidia"

    def get_model_name(self) -> str:
        return self.model

    def extrair(
        self,
        conteudo_documento: str | bytes,
        prompt_template: str,
        schema_esperado: dict,
        is_multimodal: bool = False,
    ) -> dict[str, Any]:
        """Extract data using NVIDIA API (OpenAI-compatible)."""
        import httpx

        start_time = time.time()

        # Build messages
        messages = self._build_messages(
            conteudo_documento, prompt_template, is_multimodal
        )

        # Select model based on modality
        active_model = self.vision_model if is_multimodal else self.model

        payload = {
            "model": active_model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4096,
        }

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
            extracted = self._parse_json_response(content)

            # Add metadata
            usage = result.get("usage", {})
            extracted["_metadata"] = {
                "provider": "nvidia",
                "model": active_model,
                "tempo_resposta_ms": elapsed_ms,
                "tokens_utilizados": usage.get("total_tokens"),
            }

            logger.info(
                f"NVIDIA extraction completed in {elapsed_ms}ms "
                f"using model {active_model}"
            )
            return extracted

        except httpx.HTTPStatusError as e:
            logger.error(f"NVIDIA HTTP error: {e.response.status_code} — {e.response.text}")
            raise LLMExtractionError(f"NVIDIA returned error: {e.response.status_code}") from e
        except httpx.ConnectError:
            logger.error("Cannot connect to NVIDIA API")
            raise LLMExtractionError("Cannot connect to NVIDIA API. Check network and API key.")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse NVIDIA response: {e}")
            raise LLMExtractionError("Invalid response from NVIDIA API") from e

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