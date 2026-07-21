"""Forms for the documentos app."""

from django import forms

from .models import Documento


class DocumentoUploadForm(forms.ModelForm):
    """Form for uploading a new document."""

    class Meta:
        model = Documento
        fields = ["tipo_documento", "arquivo_original"]
        widgets = {
            "tipo_documento": forms.Select(attrs={"class": "form-select"}),
            "arquivo_original": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.jpg,.jpeg,.png,.xml",
                }
            ),
        }

    def clean_arquivo_original(self):
        """Validate file type and size."""
        arquivo = self.cleaned_data.get("arquivo_original")
        if not arquivo:
            raise forms.ValidationError("Por favor, selecione um arquivo.")

        # Check file extension
        allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".xml"]
        filename = arquivo.name.lower()
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise forms.ValidationError(
                "Formato não suportado. Use PDF, JPG, PNG ou XML."
            )

        # Check file size (4.5MB limit for direct upload)
        max_size = 4.5 * 1024 * 1024  # 4.5MB in bytes
        if arquivo.size > max_size:
            raise forms.ValidationError(
                "Arquivo excede 4.5MB. Use o upload direto para armazenamento externo."
            )

        return arquivo

    def determine_formato(self, arquivo) -> str:
        """Determine the file format from the filename."""
        filename = arquivo.name.lower()
        if filename.endswith(".xml"):
            return Documento.FormatoArquivo.XML
        elif filename.endswith((".jpg", ".jpeg", ".png")):
            return Documento.FormatoArquivo.IMAGEM
        elif filename.endswith(".pdf"):
            return Documento.FormatoArquivo.PDF
        return Documento.FormatoArquivo.PDF
