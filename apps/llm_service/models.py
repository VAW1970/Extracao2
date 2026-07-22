"""
LLM Configuration Model — stores LLM provider settings in the database.

Settings persist across serverless invocations and can be managed
via the admin UI or the dedicated config page.
"""

from django.db import models


class LLMConfig(models.Model):
    """Singleton-style model for LLM configuration.

    Uses get_or_create with a fixed pk=1 pattern so only one config exists.
    Falls back to env vars if no config is saved yet.
    """

    class ProviderChoice(models.TextChoices):
        OLLAMA = "ollama", "Ollama (Local)"
        API = "api", "API Externa"

    # Which provider to use
    provider = models.CharField(
        max_length=10,
        choices=ProviderChoice.choices,
        default=ProviderChoice.API,
        verbose_name="Provedor",
        help_text="Ollama para desenvolvimento local, API para produção.",
    )

    # ── Ollama settings ──
    ollama_host = models.URLField(
        max_length=255,
        default="http://localhost:11434",
        verbose_name="Host do Ollama",
        help_text="URL do servidor Ollama local (ex: http://localhost:11434).",
    )
    ollama_model = models.CharField(
        max_length=128,
        default="llama3",
        verbose_name="Modelo Ollama",
        help_text="Nome do modelo Ollama instalado localmente.",
    )

    # ── External API settings ──
    api_provider_name = models.CharField(
        max_length=64,
        default="gemini",
        verbose_name="Nome do Provedor API",
        help_text="Identificador do provedor (ex: gemini, openai, anthropic).",
    )
    api_base_url = models.URLField(
        max_length=255,
        default="https://generativelanguage.googleapis.com/v1beta/openai",
        verbose_name="URL Base da API",
        help_text="Endpoint base da API (compatível com OpenAI).",
    )
    api_key = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Chave de API",
        help_text="Chave secreta da API. Armazenada criptografada no banco.",
    )
    api_model = models.CharField(
        max_length=128,
        default="gemini-1.5-flash",
        verbose_name="Modelo da API",
        help_text="Nome do modelo a usar na API externa.",
    )

    # ── Common settings ──
    max_retries = models.PositiveIntegerField(
        default=2,
        verbose_name="Máximo de Tentativas",
        help_text="Número máximo de tentativas de extração antes de marcar como 'precisa revisão'.",
    )
    timeout_seconds = models.PositiveIntegerField(
        default=120,
        verbose_name="Timeout (segundos)",
        help_text="Tempo limite para chamadas ao LLM.",
    )

    # ── Metadata ──
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última atualização")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Configuração LLM"
        verbose_name_plural = "Configurações LLM"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"LLM Config: {self.get_provider_display()} — {self.active_model}"

    @property
    def active_model(self) -> str:
        """Return the model name for the currently selected provider."""
        if self.provider == self.ProviderChoice.OLLAMA:
            return self.ollama_model
        return self.api_model

    @property
    def is_configured(self) -> bool:
        """Check if the current provider has minimum required config."""
        if self.provider == self.ProviderChoice.OLLAMA:
            return bool(self.ollama_host and self.ollama_model)
        return bool(self.api_key and self.api_model and self.api_base_url)

    @classmethod
    def get_active(cls) -> "LLMConfig":
        """Get or create the singleton config instance.
        
        In production (Vercel), force API provider even if DB says ollama,
        since Ollama cannot run in serverless environment.
        """
        import os
        config, _ = cls.objects.get_or_create(pk=1)
        if os.environ.get("VERCEL") and config.provider == cls.ProviderChoice.OLLAMA:
            config.provider = cls.ProviderChoice.API
            config.api_base_url = config.api_base_url or "https://api.groq.com/openai/v1"
            config.api_model = config.api_model or "llama-3.3-70b-versatile"
        return config

    def save(self, *args, **kwargs) -> None:
        """Ensure only one config instance exists (singleton pattern)."""
        self.pk = 1
        super().save(*args, **kwargs)
