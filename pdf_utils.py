# pdf_utils.py
from pathlib import Path
from pypdf import PdfReader


def read_paper(path: str) -> str:
    """
    Read a paper from disk as plain text.

    Supports PDF (via pypdf) and falls back to UTF-8 text for .md/.txt.
    """
    suffix = Path(path).suffix.lower()

    if suffix == ".pdf":
        return extract_pdf_text(path)

    # .md / .txt and anything else assumed to be UTF-8 text
    return Path(path).read_text(encoding="utf-8")


def extract_pdf_text(path: str) -> str:
    """Extract concatenated text from all pages of a PDF."""
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(text)

    full_text = "\n\n".join(pages).strip()

    if not full_text:
        raise ValueError(
            f"No extractable text found in '{path}'. "
            "The PDF may be scanned/image-based and require OCR."
        )
    return full_text