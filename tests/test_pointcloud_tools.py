import tempfile
from pathlib import Path

import pytest

from src.tools.pointcloud.ply_reader import PLYReader
from src.tools.pointcloud.pcd_reader import PCDReader
from src.tools.pointcloud.statistics import PointCloudStatistics

class TestPLYReader:
    def test_read_ascii_ply_header(self):
        content = """ply
format ascii 1.0
element vertex 100
property float x
property float y
property float z
element face 50
property list uchar int vertex_indices
end_header
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ply", delete=False) as f:
            f.write(content)
            f.flush()

        try:
            reader = PLYReader()
            info = reader.run(f.name)
            assert info["vertex_count"] == 100
            assert info["face_count"] == 50
            assert info["format"] == "ply"
        finally:
            Path(f.name).unlink()

    def test_read_nonexistent_file(self):
        reader = PLYReader()
        with pytest.raises(FileNotFoundError):
            reader.run("/nonexistent.ply")

    def test_read_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ply", delete=False) as f:
            f.write("")
            f.flush()

        try:
            reader = PLYReader()
            with pytest.raises(ValueError):
                reader.run(f.name)
        finally:
            Path(f.name).unlink()

class TestPCDReader:
    def test_read_pcd_header(self):
        content = """# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z
SIZE 4 4 4
TYPE F F F
COUNT 1 1 1
WIDTH 200
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS 200
DATA ascii"""

