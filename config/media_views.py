"""
Custom view to serve media files in production (without DEBUG=True).

This replaces the django.conf.urls.static.static() function which
returns empty list when DEBUG=False.
"""

import os
from urllib.parse import unquote
from pathlib import Path

from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.utils.http import http_date
from django.views.static import serve as django_serve


def serve_media(request, path, document_root=None):
    """
    Serve media files in production.
    
    This is a copy of django.views.static.serve but without the DEBUG check.
    """
    if document_root is None:
        document_root = settings.MEDIA_ROOT
    
    # Normalize path
    path = unquote(path)
    
    # Security check - prevent directory traversal
    document_root = Path(document_root).resolve()
    requested_path = (document_root / path).resolve()
    
    try:
        requested_path.relative_to(document_root)
    except ValueError:
        raise Http404("File not found")
    
    if not requested_path.is_file():
        raise Http404("File not found")
    
    # Use Django's serve function which handles Range headers, etc.
    return django_serve(request, path, document_root=str(document_root))