from pathlib import Path

from src.tools.file_readers.base_reader import BaseFileReader

class DOCXReader(BaseFileReader):
    @property
    def name(self) -> str:
        return "docx_reader"

    @property
    def description(self) -> str:
        return "Extract text from DOCX files."

    @property
    def supported_extensions(self) -> list[str]:
        return [".docx"]

    def read(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required to read DOCX files. Install with: pip install python-docx")

        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
