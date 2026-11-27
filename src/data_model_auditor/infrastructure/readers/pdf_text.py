"""Extract text from a modeling PDF without activating rules."""

from hashlib import sha256
from pathlib import Path

import pymupdf

from data_model_auditor.domain.reference_catalog import PdfExtraction, PdfPageText

_MAX_BYTES = 20 * 1024 * 1024


class PdfReadError(Exception):
    """Raised when a PDF cannot be read safely."""


def extract_pdf_text(path: Path) -> PdfExtraction:
    """Return page text for human review. Rules stay inactive."""
    if not path.is_file():
        raise PdfReadError(f"File not found: {path.name}")
    payload = path.read_bytes()
    if len(payload) > _MAX_BYTES:
        raise PdfReadError("The PDF exceeds the size limit.")
    if path.suffix.lower() != ".pdf":
        raise PdfReadError("The modeling standard must be a PDF file.")
    try:
        pages = _page_texts(payload)
    except PdfReadError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise PdfReadError("The PDF could not be read.") from exc
    return PdfExtraction(
        sha256=sha256(payload).hexdigest(),
        pages=pages,
        rules_active=False,
    )


def _page_texts(payload: bytes) -> tuple[PdfPageText, ...]:
    # PyMuPDF does not publish type stubs, so this boundary stays local.
    document = pymupdf.open(stream=payload, filetype="pdf")  # type: ignore[no-untyped-call]
    try:
        if bool(document.is_encrypted) and bool(document.needs_pass):
            raise PdfReadError("Encrypted PDFs are not accepted.")
        page_count = int(document.page_count)
        pages: list[PdfPageText] = []
        for index in range(page_count):
            page = document.load_page(index)  # type: ignore[no-untyped-call]
            pages.append(PdfPageText(number=index + 1, text=str(page.get_text("text"))))
        return tuple(pages)
    finally:
        document.close()  # type: ignore[no-untyped-call]
