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
        raise PDFExtractionError(f'PDF okunamadı, dosya bozuk olabilir: {exc}') from exc

    if reader.is_encrypted:
        raise PDFExtractionError('Bu PDF şifreli/korumalı. Lütfen şifresiz bir kopya yükle.')

    pages_text = [page.extract_text() or '' for page in reader.pages]
    text = '\n'.join(pages_text).strip()

    if len(text) < 50:
        raise PDFExtractionError(
            "PDF'ten yeterli metin çıkarılamadı — muhtemelen taranmış bir görüntü "
            "(OCR gerektiriyor). Lütfen metin tabanlı bir CV PDF'i yükle."
        )

    return text
