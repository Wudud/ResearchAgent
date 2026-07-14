import logging
from pathlib import Path

from src.tools.file_readers.base_reader import BaseFileReader

class PDFReader(BaseFileReader):
    @property
    def name(self) -> str:
        return "pdf_reader"

    @property
    def description(self) -> str:
        return "Extract text from PDF files."

    @property
    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def read(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("pypdf is required to read PDF files. Install with: pip install pypdf")

        reader = PdfReader(str(path))
        parts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                parts.append(text)

        return "\n\n".join(parts)
