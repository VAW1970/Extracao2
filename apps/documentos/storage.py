"""
Storage backend abstraction for file uploads.

In development: local filesystem storage.
In production (Vercel): Vercel Blob Storage via django-storages.

The storage backend is selected via the STORAGES config in settings.py.
This module provides helper functions for storage operations.
"""

import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage


def get_storage():
    """Return the configured default storage backend."""
    return default_storage


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to ensure file immutability.

    Original files are never overwritten — each upload gets a unique path.
    """
    ext = Path(original_filename).suffix.lower()
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}{ext}"


def get_upload_path(instance, filename: str) -> str:
    """Generate the upload path for a Documento file.

    Format: documentos/YYYY/MM/unique_filename
    Ensures files are never overwritten.
    """
    from django.utils import timezone

    now = timezone.now()
    unique_name = generate_unique_filename(filename)
    return f"documentos/{now.year}/{now.month:02d}/{unique_name}"


def save_file(file_obj, upload_path: str) -> str:
    """Save a file using the configured storage backend.

    Returns the stored file path.
    """
    storage = get_storage()
    saved_path = storage.save(upload_path, file_obj)
    return saved_path


def file_exists(file_path: str) -> bool:
    """Check if a file exists in the storage backend."""
    storage = get_storage()
    return storage.exists(file_path)


def delete_file(file_path: str) -> None:
    """Delete a file from the storage backend.

    Note: In production, this marks the file as deleted in the Blob storage.
    Original files should generally not be deleted (immutability).
    """
    storage = get_storage()
    if storage.exists(file_path):
        storage.delete(file_path)


def get_file_url(file_path: str) -> str:
    """Get the URL for accessing a stored file."""
    storage = get_storage()
    return storage.url(file_path)
