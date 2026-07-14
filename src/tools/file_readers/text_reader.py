from pathlib import Path

from src.tools.file_readers.base_reader import BaseFileReader

class TextReader(BaseFileReader):
    @property
    def name(self) -> str:
        return "text_reader"

    @property
    def description(self) -> str:
        return "Read plain text files."

    @property
    def supported_extensions(self) -> list[str]:
        return [".txt"]

    def read(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
