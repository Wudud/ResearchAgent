import hashlib
from pathlib import Path

from src.tools.base_tool import BaseTool

class ChecksumTool(BaseTool):
    @property
    def name(self) -> str:
        return "checksum"

    @property
    def description(self) -> str:
        return "Compute or verify MD5/SHA256 checksums for files."

    def run(self, file_path: str, algorithm: str = "md5", **kwargs) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        h = hashlib.new(algorithm)

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)

        return h.hexdigest()

    def verify(self, file_path: str, expected_hash: str, algorithm: str = "md5") -> bool:
        actual = self.run(file_path=file_path, algorithm=algorithm)
        return actual == expected_hash

    def load_manifest(self, manifest_path: str) -> dict[str, str]:
        """Load a checksum manifest file (md5sum format: MD5  path)."""
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        entries = {}
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    entries[parts[1].strip()] = parts[0].strip()
        return entries
