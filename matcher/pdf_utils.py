import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PDFExtractionError(Exception):
    """Raised when usable text can't be extracted from an uploaded PDF."""


def extract_text(uploaded_file):
    """Extract text from an in-memory uploaded PDF.

    Reads straight from Django's in-memory upload object — the PDF is never
    written to disk, only the extracted text goes on to be stored.
    """
    try:
        reader = PdfReader(io.BytesIO(uploaded_file.read()))
    except PdfReadError as exc:
        raise PDFExtractionError(f'Could not read the PDF, the file may be corrupted: {exc}') from exc

    if reader.is_encrypted:
        raise PDFExtractionError('This PDF is encrypted/password-protected. Please upload an unprotected copy.')

    pages_text = [page.extract_text() or '' for page in reader.pages]
    text = '\n'.join(pages_text).strip()

    if len(text) < 50:
        raise PDFExtractionError(
            "Couldn't extract enough text from the PDF — it's likely a scanned "
            "image (needs OCR). Please upload a text-based CV PDF."
        )

    return text
