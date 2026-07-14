import os
from pathlib import Path

from src.tools.base_tool import BaseTool

class FileScanner(BaseTool):
    @property
    def name(self) -> str:
        return "file_scanner"

    @property
    def description(self) -> str:
        return "Scan a directory and return file paths, sizes, and extensions."

    def run(self, root_path: str, allowed_extensions: list[str] | None = None, **kwargs):
        root = Path(root_path)
        if not root.exists():
            raise FileNotFoundError(f"Directory not found: {root_path}")

        files = []
        for entry in root.rglob("*"):
            if not entry.is_file():
                continue
            if allowed_extensions and entry.suffix.lower() not in allowed_extensions:
                continue
            files.append({
                "path": str(entry.relative_to(root)),
                "absolute_path": str(entry),
                "size_bytes": entry.stat().st_size,
                "extension": entry.suffix.lower(),
            })

        return files
