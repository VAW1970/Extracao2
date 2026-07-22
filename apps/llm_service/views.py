"""
LLM Configuration Views — UI for managing LLM provider settings.
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from .forms import LLMConfigForm
from .models import LLMConfig

logger = logging.getLogger("apps.llm_service")


class LLMConfigView(LoginRequiredMixin, TemplateView):
    """LLM configuration page — choose provider, set API key, pick model."""

    template_name = "llm_service/config.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = LLMConfig.get_active()
        context["form"] = LLMConfigForm(instance=config)
        context["config"] = config
        return context

    def post(self, request, *args, **kwargs):
        config = LLMConfig.get_active()
        form = LLMConfigForm(request.POST, instance=config)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "✅ Configuração do LLM salva com sucesso!",
            )
            return redirect("llm_service:config")
        else:
            messages.error(request, "❌ Erro ao salvar configuração. Verifique os campos.")
            context = self.get_context_data(**kwargs)
            context["form"] = form
            return self.render_to_response(context)


class LLMTestConnectionView(LoginRequiredMixin, View):
    """AJAX endpoint to test LLM connectivity."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            provider_type = data.get("provider", "ollama")

            config = LLMConfig.get_active()

            if provider_type == "ollama":
                import httpx

                # Only use the stored host from the database — never accept from client
                host = config.ollama_host.rstrip("/")
                try:
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.get(f"{host}/api/tags")
                        resp.raise_for_status()
                    models_data = resp.json()
                    model_names = [m["name"] for m in models_data.get("models", [])]
                    return JsonResponse(
                        {
                            "success": True,
                            "message": f"Conectado ao Ollama em {host}",
                            "models": model_names,
                        }
                    )
                except httpx.ConnectError:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f"Não foi possível conectar ao Ollama em {host}. "
                            "Verifique se o Ollama está rodando.",
                        }
                    )
                except Exception as e:
                    return JsonResponse(
                        {"success": False, "message": f"Erro ao conectar: {str(e)}"}
                    )

            elif provider_type == "api":
                import httpx
                import os

                # In production, use env var API key; otherwise use DB config
                is_production = os.environ.get("VERCEL", False)
                if is_production:
                    from django.conf import settings as dj_settings
                    api_key = dj_settings.LLM_API_KEY
                    base_url = dj_settings.LLM_BASE_URL.rstrip("/")
                else:
                    api_key = config.api_key
                    base_url = config.api_base_url.rstrip("/")

                if not api_key:
                    return JsonResponse(
                        {"success": False, "message": "Chave de API não configurada. Salve a configuração primeiro."}
                    )

                try:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    }
                    with httpx.Client(timeout=15.0) as client:
                        resp = client.get(
                            f"{base_url}/models",
                            headers=headers,
                        )
                        resp.raise_for_status()
                    models_data = resp.json()
                    model_names = [
                        m["id"] for m in models_data.get("data", [])
                    ]
                    return JsonResponse(
                        {
                            "success": True,
                            "message": f"Conectado a {base_url}",
                            "models": model_names[:50],  # limit display
                        }
                    )
                except httpx.ConnectError:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f"Não foi possível conectar a {base_url}.",
                        }
                    )
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        return JsonResponse(
                            {
                                "success": False,
                                "message": "Chave de API inválida (Erro 401).",
                            }
                        )
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f"Erro HTTP {e.response.status_code}: {e.response.text[:200]}",
                        }
                    )
                except Exception as e:
                    return JsonResponse(
                        {"success": False, "message": f"Erro ao conectar: {str(e)}"}
                    )
            else:
                return JsonResponse(
                    {"success": False, "message": f"Provedor desconhecido: {provider_type}"}
                )

        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Dados inválidos na requisição."}
            )
