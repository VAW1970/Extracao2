"""
LLM Configuration Form — manages provider settings via a single form.
"""

from django import forms

from .models import LLMConfig


class LLMConfigForm(forms.ModelForm):
    """Form for editing LLM provider configuration."""

    api_key = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Cole sua chave de API aqui...",
                "autocomplete": "off",
            }
        ),
        required=False,
        label="Chave de API",
        help_text="Sua chave secreta nunca será exibida novamente.",
    )

    class Meta:
        model = LLMConfig
        fields = [
            "provider",
            "ollama_host",
            "ollama_model",
            "api_provider_name",
            "api_base_url",
            "api_key",
            "api_model",
            "max_retries",
            "timeout_seconds",
        ]
        widgets = {
            "provider": forms.Select(attrs={"class": "form-select", "id": "provider-select"}),
            "ollama_host": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "http://localhost:11434"}
            ),
            "ollama_model": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "llama3"}
            ),
            "api_provider_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "groq"}
            ),
            "api_base_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://api.groq.com/openai/v1",
                }
            ),
            "api_model": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "llama-3.3-70b-versatile"}
            ),
            "max_retries": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 5}
            ),
            "timeout_seconds": forms.NumberInput(
                attrs={"class": "form-control", "min": 30, "max": 300}
            ),
        }

    def clean_api_key(self) -> str:
        """Preserve existing API key if the field is left empty."""
        api_key = self.cleaned_data.get("api_key", "")
        if not api_key and self.instance and self.instance.api_key:
            # Keep the existing key if user didn't enter a new one
            return self.instance.api_key
        return api_key
