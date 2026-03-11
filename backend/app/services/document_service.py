"""
Document Processing Service
Handles PDF parsing with PyMuPDF and OCR with PaddleOCR.
Enhanced for messy, scanned Indian-context PDFs with preprocessing and
multilingual support (English + Hindi/Devanagari).
"""

import os
import io
import logging
import re
from typing import Optional, List, Dict, Any

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

# Indian document type patterns for auto-detection
INDIAN_DOC_PATTERNS = {
    "gst_return": [
        r"GSTR[\s-]?[123AB]", r"Goods\s+and\s+Services\s+Tax",
        r"GSTIN", r"Tax\s+Period", r"Place\s+of\s+Supply",
    ],
    "annual_report": [
        r"Annual\s+Report", r"Director[s']?\s+Report",
        r"Auditor[s']?\s+Report", r"Schedule\s+to\s+Accounts",
    ],
    "financial_statement": [
        r"Balance\s+Sheet", r"Profit\s+and\s+Loss",
        r"Statement\s+of\s+Changes\s+in\s+Equity",
        r"Cash\s+Flow\s+Statement", r"Notes\s+to\s+(?:the\s+)?Financial\s+Statements",
        r"Ind[\s-]?AS", r"Schedule\s+III",
    ],
    "bank_statement": [
        r"Account\s+Statement", r"Transaction\s+Details",
        r"Opening\s+Balance", r"Closing\s+Balance", r"IFSC",
    ],
    "rating_report": [
        r"CRISIL|ICRA|CARE|India\s+Ratings|Brickwork|Acuit[eé]",
        r"Credit\s+Rating", r"Rating\s+Rationale",
    ],
    "legal_notice": [
        r"NCLT|NCLAT|DRT|High\s+Court|Supreme\s+Court",
        r"Legal\s+Notice", r"Arbitration", r"Writ\s+Petition",
    ],
    "itr_form": [
        r"Income\s+Tax\s+Return", r"ITR[\s-]?[1-7V]",
        r"Assessment\s+Year", r"Permanent\s+Account\s+Number",
    ],
    "cibil_report": [
        r"CIBIL|TransUnion|Credit\s+Information\s+Report",
        r"Credit\s+Score", r"DPD", r"Days\s+Past\s+Due",
        r"Commercial\s+Credit\s+Report", r"CIBIL\s+Rank",
    ],
    "mca_filing": [
        r"Ministry\s+of\s+Corporate\s+Affairs", r"MCA",
        r"Form\s+(?:MGT|AOC|SH|DIR|CHG|INC)",
        r"Annual\s+Return.*(?:u/s|under\s+section)\s+92",
    ],
}


class DocumentProcessor:
    """Processes PDF documents using PyMuPDF and PaddleOCR.
    Enhanced with image preprocessing for scanned docs,
    multilingual OCR, confidence scoring, and Indian doc recognition."""

    def __init__(self):
        self._ocr_en = None
        self._ocr_multi = None

    @property
    def ocr(self):
        """Lazy-load PaddleOCR (English) to avoid slow startup."""
        if self._ocr_en is None:
            from paddleocr import PaddleOCR
            self._ocr_en = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        return self._ocr_en

    @property
    def ocr_multilingual(self):
        """Lazy-load PaddleOCR with Hindi+English for bilingual Indian docs."""
        if self._ocr_multi is None:
            from paddleocr import PaddleOCR
            try:
                self._ocr_multi = PaddleOCR(use_angle_cls=True, lang="hi", show_log=False)
            except Exception:
                logger.info("Hindi OCR model not available, falling back to English")
                self._ocr_multi = self.ocr
        return self._ocr_multi

    def extract_text_from_pdf(self, file_path: str) -> dict:
        """
        Extract text from a PDF file. Uses intelligent OCR fallback for scanned
        documents with image preprocessing for better accuracy on Indian PDFs.

        Returns:
            dict with keys: text, ocr_used, page_count, confidence,
                            detected_doc_type, tables_extracted
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = fitz.open(file_path)
        page_count = len(doc)
        full_text = ""
        ocr_used = False
        total_confidence = 0.0
        pages_with_confidence = 0

        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text("text")

            # Smarter OCR detection: check for garbled text, not just length
            needs_ocr = self._needs_ocr(text, page)

            if needs_ocr:
                ocr_text, confidence = self._ocr_page_enhanced(page)
                if ocr_text:
                    text = ocr_text
                    ocr_used = True
                    total_confidence += confidence
                    pages_with_confidence += 1

            full_text += f"\n--- Page {page_num + 1} ---\n{text}"

        # Also extract tabular data for structured information
        tables = self._extract_tables(doc)
        if tables:
            full_text += "\n\n--- Extracted Tables ---\n"
            for t in tables:
                full_text += f"\n[Table from Page {t['page']}]\n"
                for row in t["data"]:
                    full_text += " | ".join(str(cell or "") for cell in row) + "\n"

        doc.close()

        cleaned_text = self._clean_text(full_text)
        detected_type = self._detect_indian_doc_type(cleaned_text)
        avg_confidence = (total_confidence / pages_with_confidence) if pages_with_confidence > 0 else 1.0

        return {
            "text": cleaned_text,
            "ocr_used": ocr_used,
            "page_count": page_count,
            "confidence": round(avg_confidence, 3),
            "detected_doc_type": detected_type,
            "tables_extracted": len(tables),
        }

    def _needs_ocr(self, text: str, page) -> bool:
        """Determine if a page needs OCR based on multiple heuristics."""
        stripped = text.strip()

        # Very little text extracted
        if len(stripped) < 50:
            return True

        # Check for high ratio of garbled/non-ASCII characters (common in bad extraction)
        if stripped:
            non_ascii = sum(1 for c in stripped if ord(c) > 127 and c not in '₹€£¥°')
            garbled_ratio = non_ascii / len(stripped)
            if garbled_ratio > 0.3:
                return True

        # Check if page has significant images (likely scanned)
        image_list = page.get_images(full=True)
        page_area = page.rect.width * page.rect.height
        if image_list and len(stripped) < 200:
            return True

        # Check for very low word density (garbled OCR artifact)
        words = stripped.split()
        if len(words) > 0:
            avg_word_len = sum(len(w) for w in words) / len(words)
            if avg_word_len < 2 or avg_word_len > 25:
                return True

        return False

    def _ocr_page_enhanced(self, page) -> tuple:
        """Run OCR with image preprocessing for better accuracy on Indian docs.
        Returns (text, confidence_score)."""
        try:
            # Render at high DPI for scanned documents
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))

            # Preprocess image for better OCR
            img = self._preprocess_image(img)

            img_array = np.array(img)

            # Try English OCR first
            result = self.ocr.ocr(img_array, cls=True)
            text_en, conf_en = self._parse_ocr_result(result)

            # If confidence is low, try multilingual (Hindi+English) OCR
            if conf_en < 0.7 and self.ocr_multilingual != self.ocr:
                result_multi = self.ocr_multilingual.ocr(img_array, cls=True)
                text_multi, conf_multi = self._parse_ocr_result(result_multi)
                if conf_multi > conf_en:
                    return text_multi, conf_multi

            return text_en, conf_en

        except Exception as e:
            logger.warning(f"Enhanced OCR failed for page: {e}")
            # Fallback to basic OCR
            return self._ocr_page_basic(page)

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """Preprocess scanned image for better OCR accuracy."""
        # Convert to grayscale
        if img.mode != 'L':
            img = img.convert('L')

        # Enhance contrast (helps with faded scans)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # Sharpen (helps with blurry scans)
        img = img.filter(ImageFilter.SHARPEN)

        # Adaptive thresholding simulation via autocontrast
        from PIL import ImageOps
        img = ImageOps.autocontrast(img, cutoff=2)

        # Convert back to RGB for PaddleOCR
        img = img.convert('RGB')

        return img

    def _parse_ocr_result(self, result) -> tuple:
        """Parse PaddleOCR result into text and average confidence."""
        if not result or not result[0]:
            return "", 0.0

        lines = []
        confidences = []
        for line in result[0]:
            if line and len(line) >= 2:
                text = line[1][0]
                conf = line[1][1]
                lines.append(text)
                confidences.append(conf)

        text = "\n".join(lines)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return text, avg_conf

    def _ocr_page_basic(self, page) -> tuple:
        """Basic OCR fallback without preprocessing."""
        try:
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            img_array = np.array(img)
            result = self.ocr.ocr(img_array, cls=True)
            return self._parse_ocr_result(result)
        except Exception as e:
            logger.warning(f"Basic OCR also failed: {e}")
            return "", 0.0

    def _detect_indian_doc_type(self, text: str) -> Optional[str]:
        """Auto-detect Indian document type from extracted text content."""
        text_upper = text[:5000].upper()
        scores = {}
        for doc_type, patterns in INDIAN_DOC_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_upper, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[doc_type] = score

        if scores:
            return max(scores, key=scores.get)
        return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text, preserving Indian-specific content."""
        # Preserve Indian currency symbols and common markers
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Keep Indian script characters (Devanagari range) and common symbols
        text = re.sub(r'[^\x20-\x7E\n\t\u0900-\u097F\u20B9₹]', ' ', text)
        # Collapse multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        # Normalize Indian number formats (lakhs/crores separators)
        # e.g., "1,23,456" should be preserved, not mangled
        # Fix common OCR artifacts in Indian documents
        text = re.sub(r'(?i)\bRs\s*\.?\s*', '₹', text)
        text = re.sub(r'(?i)\bINR\s+', '₹', text)
        return text.strip()

    def _extract_tables(self, doc) -> list:
        """Extract tabular data from PDF pages."""
        tables = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            try:
                tab_finder = page.find_tables()
                for table in tab_finder.tables:
                    extracted = table.extract()
                    if extracted and len(extracted) > 1:  # At least header + 1 row
                        tables.append({
                            "page": page_num + 1,
                            "data": extracted,
                        })
            except Exception:
                continue
        return tables

    def extract_tables_from_pdf(self, file_path: str) -> list:
        """Extract tabular data from PDF pages (public API)."""
        doc = fitz.open(file_path)
        tables = self._extract_tables(doc)
        doc.close()
        return tables


# Singleton instance
document_processor = DocumentProcessor()
