"""
PDF Preprocessor — extracts text from PDF files using pdfplumber.

pdfplumber is a pure-Python library compatible with the Vercel serverless runtime.
For scanned PDFs (no extractable text), the content is returned as bytes
for multimodal LLM processing.
"""

import logging
from pathlib import Path
from io import BytesIO

logger = logging.getLogger("apps.llm_service")


class PDFPreprocessor:
    """Extract text content from PDF files using pdfplumber."""

    def preprocess(self, file_path: str | Path | BytesIO) -> dict:
        """Preprocess a PDF file.

        Args:
            file_path: Path to the PDF file or a BytesIO stream.
        """
        import pdfplumber

        result = {
            "text": None,
            "is_scanned": False,
            "page_count": 0,
            "char_count": 0,
        }

        try:
            with pdfplumber.open(file_path) as pdf:
                result["page_count"] = len(pdf.pages)
                full_text = []

                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text.append(text.strip())

                combined_text = "\n\n".join(full_text)

                if combined_text.strip():
                    result["text"] = combined_text
                    result["char_count"] = len(combined_text)
                    logger.info(
                        f"PDF preprocessed: {result['page_count']} pages, "
                        f"{result['char_count']} chars extracted"
                    )
                else:
                    # No text extracted — likely a scanned PDF
                    result["is_scanned"] = True
                    logger.info("PDF appears to be scanned (no text extracted)")

        except Exception as e:
            logger.error(f"Error preprocessing PDF {file_path}: {e}")
            raise

        return result

    def get_image_bytes(self, file_path) -> bytes:
        """Return raw bytes from PDF for multimodal LLM processing."""
        if isinstance(file_path, (str, Path)):
            with open(file_path, "rb") as f:
                return f.read()
        # Assumed BytesIO or file-like
        file_path.seek(0)
        return file_path.read()
