"""
PDF extraction module for BLMID Validator.
Extracts BLMID and coordinates from PDF forms.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract BLMID and coordinates from PDF files."""

    def __init__(
        self,
        blmid_pattern: Optional[str] = None,
        latitude_pattern: Optional[str] = None,
        longitude_pattern: Optional[str] = None,
        ocr_enabled: bool = True,
        ocr_fallback: bool = True,
        tesseract_path: Optional[str] = None,
    ):
        """
        Initialize PDF extractor.

        Args:
            blmid_pattern: Regex pattern for BLMID (if None, uses generic pattern)
            latitude_pattern: Regex pattern for latitude
            longitude_pattern: Regex pattern for longitude
            ocr_enabled: Enable OCR processing
            ocr_fallback: Use OCR only if text extraction fails
            tesseract_path: Path to tesseract executable
        """
        self.blmid_pattern = blmid_pattern or r"BLM[\s-]*(?:ID)?[\s-]*([A-Z0-9]+)"
        self.latitude_pattern = latitude_pattern or r"(lat[a-z]*|latitude)[\s:]*(-?\d+\.?\d*)"
        self.longitude_pattern = (
            longitude_pattern or r"(lon[a-z]*|longitude)[\s:]*(-?\d+\.?\d*)"
        )
        self.ocr_enabled = ocr_enabled
        self.ocr_fallback = ocr_fallback
        self.tesseract_path = tesseract_path

        if self.tesseract_path and pytesseract:
            pytesseract.pytesseract.pytesseract_cmd = self.tesseract_path

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract BLMID and coordinates from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with keys: blmid, latitude, longitude, text, errors
        """
        result = {
            "blmid": None,
            "latitude": None,
            "longitude": None,
            "text": "",
            "errors": [],
        }

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            result["errors"].append(f"PDF file not found: {pdf_path}")
            logger.error(f"PDF file not found: {pdf_path}")
            return result

        try:
            # Try text extraction first
            text = self._extract_text(str(pdf_path))
            result["text"] = text

            if text.strip():
                # Extract values from text
                self._extract_from_text(text, result)
            else:
                # No text; try OCR if enabled
                if self.ocr_enabled:
                    logger.info(f"No text in PDF {pdf_path.name}; attempting OCR...")
                    text = self._extract_text_ocr(str(pdf_path))
                    if text.strip():
                        result["text"] = text
                        self._extract_from_text(text, result)
                    else:
                        result["errors"].append("OCR extraction failed")
                else:
                    result["errors"].append("PDF contains no extractable text")

        except Exception as e:
            logger.error(f"Error extracting from {pdf_path}: {e}")
            result["errors"].append(str(e))

        return result

    def _extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber or PyPDF2."""
        text = ""

        # Try pdfplumber first (better for structured PDFs)
        if pdfplumber:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                        # Also try table extraction
                        tables = page.extract_tables()
                        if tables:
                            for table in tables:
                                for row in table:
                                    text += " ".join(str(cell) for cell in row if cell) + "\n"
                return text
            except Exception as e:
                logger.debug(f"pdfplumber extraction failed for {pdf_path}: {e}")

        # Fallback to PyPDF2
        if PyPDF2:
            try:
                with open(pdf_path, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                return text
            except Exception as e:
                logger.debug(f"PyPDF2 extraction failed for {pdf_path}: {e}")

        return text

    def _extract_text_ocr(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR (converts to images first)."""
        if not pytesseract or not Image:
            logger.warning("pytesseract or Pillow not available; OCR skipped")
            return ""

        text = ""
        try:
            # Try converting PDF to images and OCR each
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(pdf_path)
                for page_num, page in enumerate(doc):
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution
                    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text += pytesseract.image_to_string(image) + "\n"
                doc.close()
            except ImportError:
                logger.warning("PyMuPDF not available; OCR skipped")
                return ""
        except Exception as e:
            logger.error(f"OCR extraction failed for {pdf_path}: {e}")

        return text

    def _extract_from_text(self, text: str, result: Dict) -> None:
        """Extract BLMID and coordinates from text."""
        text_upper = text.upper()

        # Extract BLMID
        blmid_match = re.search(self.blmid_pattern, text_upper, re.IGNORECASE)
        if blmid_match:
            result["blmid"] = blmid_match.group(1).strip() if blmid_match.lastindex else blmid_match.group(0)
        else:
            result["errors"].append("BLMID not found in PDF")

        # Extract latitude
        lat_match = re.search(self.latitude_pattern, text, re.IGNORECASE)
        if lat_match:
            try:
                result["latitude"] = float(lat_match.group(2))
            except (ValueError, IndexError):
                result["errors"].append("Latitude extraction failed")
        else:
            result["errors"].append("Latitude not found in PDF")

        # Extract longitude
        lon_match = re.search(self.longitude_pattern, text, re.IGNORECASE)
        if lon_match:
            try:
                result["longitude"] = float(lon_match.group(2))
            except (ValueError, IndexError):
                result["errors"].append("Longitude extraction failed")
        else:
            result["errors"].append("Longitude not found in PDF")

    def batch_extract(self, pdf_dir: str) -> List[Dict]:
        """
        Extract from all PDFs in a directory.

        Args:
            pdf_dir: Directory containing PDF files

        Returns:
            List of extraction results
        """
        pdf_dir = Path(pdf_dir)
        results = []

        pdf_files = list(pdf_dir.glob("*.pdf")) + list(pdf_dir.glob("*.PDF"))
        logger.info(f"Found {len(pdf_files)} PDF files in {pdf_dir}")

        for pdf_file in pdf_files:
            logger.info(f"Extracting from {pdf_file.name}...")
            result = self.extract_from_pdf(str(pdf_file))
            result["pdf_file"] = pdf_file.name
            results.append(result)

        return results
