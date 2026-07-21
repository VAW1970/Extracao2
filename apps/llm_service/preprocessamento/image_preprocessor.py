"""
Image Preprocessor — prepares images for multimodal LLM processing.

NO dependency on pytesseract/Tesseract (not guaranteed on Vercel runtime).
Images are sent directly to a multimodal LLM (vision model) for extraction.
"""

import logging
from pathlib import Path

logger = logging.getLogger("apps.llm_service")


class ImagePreprocessor:
    """Prepare images for multimodal LLM processing.

    This preprocessor does NOT perform OCR locally. Instead, it prepares
    the image bytes to be sent directly to a vision-capable LLM.
    """

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    def preprocess(self, file_path: str | Path) -> dict:
        """Prepare an image for multimodal LLM processing.

        Args:
            file_path: Path to the image file.

        Returns:
            dict with keys:
                - image_bytes: raw image bytes for the LLM
                - format: image format (jpg, png)
                - is_multimodal: always True for images
                - file_size: size in bytes
        """
        file_path = Path(file_path)

        # Validate file extension
        if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format: {file_path.suffix}. "
                f"Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        result = {
            "image_bytes": None,
            "format": file_path.suffix.lower().lstrip("."),
            "is_multimodal": True,
            "file_size": file_path.stat().st_size,
        }

        try:
            with open(file_path, "rb") as f:
                result["image_bytes"] = f.read()

            logger.info(
                f"Image preprocessed: {result['format']}, "
                f"{result['file_size']} bytes, ready for multimodal LLM"
            )

        except Exception as e:
            logger.error(f"Error preprocessing image {file_path}: {e}")
            raise

        return result

    def get_base64(self, file_path: str | Path) -> str:
        """Get the image as a base64 string for API transmission."""
        import base64

        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
