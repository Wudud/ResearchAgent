import logging
from pathlib import Path

from src.dataset.models import DatasetInventory, FileEntry
from src.tools.filesystem.scanner import FileScanner
from src.tools.filesystem.checksum import ChecksumTool

class DatasetScanner:
    def __init__(self, allowed_extensions: list[str] | None = None):
        self._file_scanner = FileScanner()
        self._checksum = ChecksumTool()
        self._allowed_extensions = allowed_extensions or [".ply", ".pcd", ".pts", ".xyz", ".xyzrgb", ".npy"]
        self._logger = logging.getLogger("ResearchAgent.DatasetScanner")

    def scan(self, root_path: str) -> DatasetInventory:
        root = Path(root_path)
        if not root.exists():
            raise FileNotFoundError(f"Dataset directory not found: {root_path}")

        self._logger.info(f"Scanning dataset: {root_path}")

        raw_files = self._file_scanner.run(
            root_path=str(root), allowed_extensions=self._allowed_extensions
        )

        files = []
        total_size = 0
        ext_counts: dict[str, int] = {}

        for rf in raw_files:
            md5 = self._checksum.run(rf["absolute_path"])
            entry = FileEntry(
                relative_path=rf["path"],
                absolute_path=rf["absolute_path"],
                size_bytes=rf["size_bytes"],
                extension=rf["extension"],
                md5_hex=md5,
            )
            files.append(entry)
            total_size += rf["size_bytes"]
            ext_counts[rf["extension"]] = ext_counts.get(rf["extension"], 0) + 1

        self._logger.info(f"Scan complete: {len(files)} files, {total_size} bytes")

        return DatasetInventory(
            root_path=str(root),
            files=files,
            total_files=len(files),
            total_size_bytes=total_size,
            extension_counts=ext_counts,
        )
