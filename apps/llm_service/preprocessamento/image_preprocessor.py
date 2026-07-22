"""
Image Preprocessor — prepares images for multimodal LLM processing.

NO dependency on pytesseract/Tesseract (not guaranteed on Vercel runtime).
Images are sent directly to a multimodal LLM (vision model) for extraction.
"""

import logging
from io import BytesIO
from pathlib import Path

logger = logging.getLogger("apps.llm_service")


class ImagePreprocessor:
    """Prepare images for multimodal LLM processing.

    This preprocessor does NOT perform OCR locally. Instead, it prepares
    the image bytes to be sent directly to a vision-capable LLM.
    """

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    def preprocess(self, file_path: str | Path | BytesIO, original_name: str = "") -> dict:
        """Prepare an image for multimodal LLM processing.

        Args:
            file_path: Path to the image file or a BytesIO stream.
            original_name: Original filename (used for extension validation
                           when file_path is a BytesIO).
        """
        # Determine the file extension
        if isinstance(file_path, BytesIO):
            suffix = Path(original_name).suffix.lower() if original_name else ".jpg"
        else:
            suffix = Path(file_path).suffix.lower()

        if suffix not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format: {suffix}. "
                f"Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Read bytes
        if isinstance(file_path, BytesIO):
            file_path.seek(0)
            image_bytes = file_path.read()
        else:
            with open(file_path, "rb") as f:
                image_bytes = f.read()

        result = {
            "image_bytes": image_bytes,
            "format": suffix.lstrip("."),
            "is_multimodal": True,
            "file_size": len(image_bytes),
        }

        logger.info(
            f"Image preprocessed: {result['format']}, "
            f"{result['file_size']} bytes, ready for multimodal LLM"
        )

        return result

    def get_base64(self, file_path: str | Path | BytesIO) -> str:
        """Get the image as a base64 string for API transmission."""
        import base64

        if isinstance(file_path, BytesIO):
            file_path.seek(0)
            return base64.b64encode(file_path.read()).decode("utf-8")
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
