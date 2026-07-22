"""
Supabase Storage backend for Django.

Uses the Supabase Storage REST API to upload/download files.
Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.

This backend is compatible with Django's FileField/ImageField and works
in serverless environments (Vercel) where the filesystem is read-only.
"""

import io
import logging
import os
from urllib.parse import quote, urljoin

import httpx
from django.core.files.base import ContentFile
from django.core.files.storage import BaseStorage
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger("apps.storage")


class SupabaseStorage(BaseStorage):
    """Django storage backend that uses Supabase Storage via REST API.

    Configuration via environment variables:
        SUPABASE_URL:             https://<project>.supabase.co
        SUPABASE_SERVICE_ROLE_KEY: service role key (server-side only)
        SUPABASE_BUCKET_NAME:     bucket name (default: "documentos")
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        self.supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self.bucket_name = os.environ.get("SUPABASE_BUCKET_NAME", "documentos")

        self._api_base = f"{self.supabase_url}/storage/v1"
        self._headers = {
            "Authorization": f"Bearer {self.supabase_key}",
            "apikey": self.supabase_key,
        }

    # ------------------------------------------------------------------
    # Required overrides
    # ------------------------------------------------------------------

    def _save(self, name, content):
        """Upload file to Supabase Storage."""
        # Clean path: remove leading slashes, normalize
        name = self._clean_name(name)
        upload_path = quote(name, safe="")

        # Read content into memory (serverless-friendly, avoids temp files)
        if hasattr(content, "read"):
            content.seek(0)
            data = content.read()
        else:
            data = content

        if isinstance(data, str):
            data = data.encode("utf-8")

        url = f"{self._api_base}/object/{self.bucket_name}/{upload_path}"
        headers = {
            **self._headers,
            "Content-Type": "application/octet-stream",
            "x-upsert": "false",
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, content=data, headers=headers)
                resp.raise_for_status()
            logger.info(f"Uploaded '{name}' to Supabase bucket '{self.bucket_name}'")
            return name
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Supabase upload failed for '{name}': "
                f"{e.response.status_code} — {e.response.text}"
            )
            raise IOError(f"Failed to upload to Supabase: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Supabase upload connection error: {e}")
            raise IOError("Cannot connect to Supabase Storage") from e

    def _open(self, name, mode="rb"):
        """Download file from Supabase Storage."""
        name = self._clean_name(name)
        download_path = quote(name, safe="")
        url = f"{self._api_base}/object/{self.bucket_name}/{download_path}"

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.get(url, headers=self._headers)
                resp.raise_for_status()
            return ContentFile(resp.content)
        except httpx.HTTPStatusError as e:
            logger.error(f"Supabase download failed for '{name}': {e.response.status_code}")
            raise FileNotFoundError(f"File not found in Supabase: {name}") from e
        except httpx.RequestError as e:
            logger.error(f"Supabase download connection error: {e}")
            raise IOError("Cannot connect to Supabase Storage") from e

    def delete(self, name):
        """Delete file from Supabase Storage."""
        name = self._clean_name(name)
        # Supabase delete expects body with prefixes
        url = f"{self._api_base}/object/{self.bucket_name}"
        headers = {**self._headers, "Content-Type": "application/json"}
        body = {"prefixes": [name]}

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.delete(url, json=body, headers=headers)
                resp.raise_for_status()
            logger.info(f"Deleted '{name}' from Supabase bucket")
        except httpx.HTTPError as e:
            logger.error(f"Supabase delete failed for '{name}': {e}")

    def exists(self, name):
        """Check if file exists in Supabase Storage."""
        name = self._clean_name(name)
        # Use list endpoint with exact path
        url = f"{self._api_base}/object/list/{self.bucket_name}"
        headers = {**self._headers, "Content-Type": "application/json"}
        folder, _, filename = name.rpartition("/")
        body = {
            "prefix": folder + "/" if folder else "",
            "limit": 1000,
            "offset": 0,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=body, headers=headers)
                resp.raise_for_status()
            files = resp.json()
            return any(f.get("name") == filename for f in files)
        except httpx.HTTPError as e:
            logger.error(f"Supabase exists check failed: {e}")
            return False

    def listdir(self, path):
        """List directory contents in Supabase Storage."""
        path = self._clean_name(path) if path else ""
        url = f"{self._api_base}/object/list/{self.bucket_name}"
        headers = {**self._headers, "Content-Type": "application/json"}
        body = {"prefix": path, "limit": 1000, "offset": 0}

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=body, headers=headers)
                resp.raise_for_status()
            items = resp.json()
            dirs, files = [], []
            for item in items:
                if item.get("id") is None:
                    dirs.append(item["name"])
                else:
                    files.append(item["name"])
            return dirs, files
        except httpx.HTTPError as e:
            logger.error(f"Supabase listdir failed: {e}")
            return [], []

    def size(self, name):
        """Get file size from Supabase Storage."""
        name = self._clean_name(name)
        # Reuse list to find metadata
        folder, _, filename = name.rpartition("/")
        url = f"{self._api_base}/object/list/{self.bucket_name}"
        headers = {**self._headers, "Content-Type": "application/json"}
        body = {"prefix": folder + "/" if folder else "", "limit": 1000, "offset": 0}

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=body, headers=headers)
                resp.raise_for_status()
            items = resp.json()
            for item in items:
                if item.get("name") == filename:
                    return item.get("metadata", {}).get("size", 0)
            return 0
        except httpx.HTTPError as e:
            logger.error(f"Supabase size failed: {e}")
            return 0

    def url(self, name):
        """Return the public URL of the file in Supabase Storage."""
        name = self._clean_name(name)
        public_url = f"{self._api_base}/object/public/{self.bucket_name}/{quote(name, safe='')}"
        return public_url

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_name(name: str) -> str:
        """Normalize path: remove leading slashes and parent refs."""
        return str(name).lstrip("/").replace("\\", "/")
