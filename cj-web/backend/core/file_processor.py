"""
Processes uploaded files (images and documents) for the chat endpoint.

Images    → encoded as base64 data-URL for the Groq Vision API.
Documents → text is extracted and injected into the RAG context.

Supported input types
─────────────────────
  Images    : image/jpeg · image/png · image/gif · image/webp
  Documents : application/pdf · text/plain
              application/vnd.openxmlformats-officedocument.wordprocessingml.document (.docx)
"""

import base64
import io
from typing import NamedTuple

from utils.logger import get_logger

logger = get_logger()

# ── Limits ────────────────────────────────────────────────────────────────────

MAX_IMAGE_BYTES = 3 * 1024 * 1024    # 3 MB  (Groq Vision cap after base64)
MAX_DOC_BYTES   = 5 * 1024 * 1024    # 5 MB
MAX_DOC_CHARS   = 8_000              # truncate long docs to keep prompts sensible

# ── Allowed MIME types ────────────────────────────────────────────────────────

ALLOWED_IMAGE_TYPES: frozenset[str] = frozenset({
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
})
ALLOWED_DOC_TYPES: frozenset[str] = frozenset({
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
})
ALLOWED_TYPES: frozenset[str] = ALLOWED_IMAGE_TYPES | ALLOWED_DOC_TYPES

# Human-readable type label shown to users
_TYPE_LABELS: dict[str, str] = {
    "image/jpeg": "JPEG",
    "image/jpg":  "JPEG",
    "image/png":  "PNG",
    "image/gif":  "GIF",
    "image/webp": "WebP",
    "application/pdf": "PDF",
    "text/plain":      "TXT",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
}


# ── Result type ───────────────────────────────────────────────────────────────

class ProcessedFile(NamedTuple):
    kind: str                        # "image" | "document"
    filename: str
    mime_type: str
    data_url: str | None = None      # images only — "data:<mime>;base64,<b64>"
    extracted_text: str | None = None  # documents only


# ── Public API ────────────────────────────────────────────────────────────────

def process_upload(filename: str, content_type: str, data: bytes) -> ProcessedFile:
    """
    Validate and process an uploaded file.

    Returns a :class:`ProcessedFile`.
    Raises :class:`ValueError` on unsupported type, size exceeded, or parse failure.
    """
    ct = _normalise_mime(content_type)

    if ct not in ALLOWED_TYPES:
        raise ValueError(
            f"Unsupported file type '{ct}'. "
            "Supported: JPEG · PNG · GIF · WebP images, PDF · TXT · DOCX documents."
        )

    if ct in ALLOWED_IMAGE_TYPES:
        return _process_image(filename, ct, data)

    return _process_document(filename, ct, data)


def _normalise_mime(raw: str) -> str:
    """Strip parameters (e.g. '; charset=utf-8') and lower-case."""
    return (raw or "").lower().split(";")[0].strip()


# ── Image handling ────────────────────────────────────────────────────────────

def _process_image(filename: str, ct: str, data: bytes) -> ProcessedFile:
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image is too large ({len(data) // 1024} KB). Maximum allowed size is 3 MB."
        )
    b64      = base64.b64encode(data).decode("ascii")
    data_url = f"data:{ct};base64,{b64}"
    logger.debug("Processed image upload: %s (%d bytes)", filename, len(data))
    return ProcessedFile(kind="image", filename=filename, mime_type=ct, data_url=data_url)


# ── Document handling ─────────────────────────────────────────────────────────

def _process_document(filename: str, ct: str, data: bytes) -> ProcessedFile:
    if len(data) > MAX_DOC_BYTES:
        raise ValueError(
            f"Document is too large ({len(data) // 1024} KB). Maximum allowed size is 5 MB."
        )

    text = _extract_text(ct, data)
    if not text.strip():
        raise ValueError(
            "Could not extract any text from the document. "
            "Make sure it is not password-protected or image-only."
        )

    if len(text) > MAX_DOC_CHARS:
        text = (
            text[:MAX_DOC_CHARS]
            + f"\n\n[Document truncated — showing first {MAX_DOC_CHARS:,} characters]"
        )

    logger.debug("Processed document upload: %s — %d chars extracted", filename, len(text))
    return ProcessedFile(
        kind="document",
        filename=filename,
        mime_type=ct,
        extracted_text=text,
    )


def _extract_text(content_type: str, data: bytes) -> str:
    if content_type == "text/plain":
        return data.decode("utf-8", errors="replace")

    if content_type == "application/pdf":
        return _pdf_to_text(data)

    if content_type == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return _docx_to_text(data)

    return ""


def _pdf_to_text(data: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        pages  = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(p for p in pages if p.strip())
    except Exception as exc:
        raise ValueError(f"Failed to read PDF: {exc}") from exc


def _docx_to_text(data: bytes) -> str:
    try:
        import docx
        doc   = docx.Document(io.BytesIO(data))
        paras = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paras)
    except Exception as exc:
        raise ValueError(f"Failed to read DOCX: {exc}") from exc
