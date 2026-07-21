"""
PDF Preprocessor — extracts text from PDF files using pdfplumber.

pdfplumber is a pure-Python library compatible with the Vercel serverless runtime.
For scanned PDFs (no extractable text), the content is returned as bytes
for multimodal LLM processing.
"""

import logging
from pathlib import Path

logger = logging.getLogger("apps.llm_service")


class PDFPreprocessor:
    """Extract text content from PDF files using pdfplumber."""

    def preprocess(self, file_path: str | Path) -> dict:
        """Preprocess a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            dict with keys:
                - text: extracted text (str or None if no text found)
                - is_scanned: bool indicating if the PDF appears scanned
                - page_count: number of pages
                - char_count: number of characters extracted
        """
        import pdfplumber

        file_path = Path(file_path)
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

    def get_image_bytes(self, file_path: str | Path) -> bytes:
        """Get the raw bytes of a PDF page for multimodal LLM processing.

        Converts the first page to an image for sending to a vision model.
        """
        # For now, return the raw PDF bytes — the multimodal LLM can handle PDFs directly
        # In a future iteration, we could convert specific pages to images
        with open(file_path, "rb") as f:
            return f.read()
