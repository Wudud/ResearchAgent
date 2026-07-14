from pathlib import Path

from src.tools.file_readers.base_reader import BaseFileReader

class MarkdownReader(BaseFileReader):
    @property
    def name(self) -> str:
        return "markdown_reader"

    @property
    def description(self) -> str:
        return "Read Markdown files."

    @property
    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown"]

    def read(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
