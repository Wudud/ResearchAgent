import logging
from pathlib import Path

from src.assistant.document import Document
from src.tools.file_readers.base_reader import BaseFileReader
from src.tools.file_readers.text_reader import TextReader
from src.tools.file_readers.pdf_reader import PDFReader
from src.tools.file_readers.docx_reader import DOCXReader
from src.tools.file_readers.markdown_reader import MarkdownReader
from src.tools.file_readers.python_reader import PythonReader
from src.tools.file_readers.excel_reader import ExcelReader
from src.tools.file_readers.image_reader import ImageReader

class FileRouter:
    def __init__(self, vision_service=None):
        self._readers: list[BaseFileReader] = [
            PDFReader(),
            DOCXReader(),
            ExcelReader(),
            ImageReader(vision_service=vision_service),
            PythonReader(),
            MarkdownReader(),
            TextReader(),
        ]
        self._logger = logging.getLogger("ResearchAgent.FileRouter")

    def route(self, file_path: str) -> Document:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        self._logger.info(f"Routing file: {path.name} (extension={ext})")

        for reader in self._readers:
            if reader.can_handle(ext):
                content = reader.read(str(path))
                doc = Document(
                    id=path.stem,
                    title=path.name,
                    type=ext.lstrip("."),
                    content=content,
                    metadata={"file_path": str(path), "size_bytes": path.stat().st_size},
                )
                self._logger.info(f"Routed to {reader.name}: {len(content)} chars")
                return doc

        raise ValueError(f"Unsupported file type: {ext}")
