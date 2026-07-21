"""Custom template tags for documents."""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="read_file")
def read_file(file_field):
    """Read the content of a FileField and return as string.

    Usage: {{ documento.arquivo_original|read_file }}
    """
    try:
        if file_field and hasattr(file_field, "open"):
            with file_field.open("r", encoding="utf-8", errors="replace") as f:
                return f.read()
        return ""
    except Exception:
        return "[Erro ao ler arquivo]"


@register.filter(name="file_size")
def file_size(file_field):
    """Return the file size in a human-readable format."""
    try:
        if file_field and hasattr(file_field, "size"):
            size = file_field.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "—"
    except Exception:
        return "—"
