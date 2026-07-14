import struct
from pathlib import Path

from src.tools.base_tool import BaseTool

class PLYReader(BaseTool):
    @property
    def name(self) -> str:
        return "ply_reader"

    @property
    def description(self) -> str:
        return "Read PLY file header to extract point count and properties."

    def run(self, file_path: str, **kwargs) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(path, "rb") as f:
                header_lines = []
                while True:
                    raw = f.readline()
                    if not raw:
                        raise ValueError("PLY file ended before 'end_header'")
                    line = raw.decode("utf-8", errors="replace").strip()
                    header_lines.append(line)
                    if line == "end_header":
                        break
                    if len(header_lines) > 1000:
                        raise ValueError("PLY header too long")

            vertex_count = 0
            face_count = 0
            properties = []

            for line in header_lines:
                if line.startswith("element vertex "):
                    vertex_count = int(line.split()[-1])
                elif line.startswith("element face "):
                    face_count = int(line.split()[-1])
                elif line.startswith("property "):
                    properties.append(line)

            return {
                "vertex_count": vertex_count,
                "face_count": face_count,
                "property_count": len(properties),
                "format": "ply",
            }
        except Exception as e:
            raise ValueError(f"Failed to read PLY file {file_path}: {e}")
