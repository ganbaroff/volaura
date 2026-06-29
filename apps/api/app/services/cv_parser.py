"""CV text extraction from PDF and DOCX files.

Sprint 1 of the CV Truth Machine (ADR-017 Layer 1).
Extracts plain text only — no images, no scans, no OCR.
Original file is NOT stored (GDPR data minimization).
"""

from __future__ import annotations

import io

from loguru import logger


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using pymupdf.

    Returns concatenated text from all pages, separated by newlines.
    Raises ValueError if the PDF has no extractable text (scanned/image PDF).
    """
    import pymupdf  # lazy import — not needed at module load

    text_parts: list[str] = []
    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text.strip())

    full_text = "\n\n".join(text_parts)
    if not full_text.strip():
        raise ValueError("PDF contains no extractable text (may be scanned/image-only)")

    logger.info("PDF parsed", pages=len(text_parts), chars=len(full_text))
    return full_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx.

    Returns concatenated paragraph text, separated by newlines.
    Raises ValueError if the document has no text content.
    """
    import docx  # lazy import

    doc = docx.Document(io.BytesIO(file_bytes))
    text_parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    full_text = "\n".join(text_parts)
    if not full_text.strip():
        raise ValueError("DOCX contains no extractable text")

    logger.info("DOCX parsed", paragraphs=len(text_parts), chars=len(full_text))
    return full_text


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from a CV file based on extension.

    Supported: .pdf, .docx
    Raises ValueError for unsupported formats or empty content.
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: {filename}. Use PDF or DOCX.")
