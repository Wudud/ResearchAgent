import re
import struct
from pathlib import Path

from src.tools.base_tool import BaseTool

class PCDReader(BaseTool):
    @property
    def name(self) -> str:
        return "pcd_reader"

    @property
    def description(self) -> str:
        return "Read PCD file header to extract point count, dimensions, and fields."

    def run(self, file_path: str, **kwargs) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(path, "rb") as f:
                header = b""
                while True:
                    chunk = f.read(1)
                    if not chunk:
                        break
                    header += chunk
                    if header.endswith(b"\n\n"):
                        break
                    if len(header) > 8192:
                        raise ValueError("PCD header too long")

            header_str = header.decode("utf-8", errors="replace")

            width = 0
            height = 0
            points = 0
            fields = []

            for line in header_str.split("\n"):
                line = line.strip()
                if line.startswith("WIDTH "):
                    width = int(line.split()[-1])
                elif line.startswith("HEIGHT "):
                    height = int(line.split()[-1])
                elif line.startswith("POINTS "):
                    points = int(line.split()[-1])
                elif line.startswith("FIELDS "):
                    fields = line.split()[1:]

            return {
                "width": width,
                "height": height,
                "point_count": max(points, width * height),
                "fields": fields,
                "field_count": len(fields),
                "format": "pcd",
            }
        except Exception as e:
            raise ValueError(f"Failed to read PCD file {file_path}: {e}")
