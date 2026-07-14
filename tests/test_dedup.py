import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.dataset.dedup import PointCloudDedupChecker

def _write_test_ply(path: str, points: np.ndarray):
    n = len(points)
    header = f"ply\nformat ascii 1.0\nelement vertex {n}\nproperty float x\nproperty float y\nproperty float z\nend_header\n"
    body = "\n".join(f"{p[0]} {p[1]} {p[2]}" for p in points)
    with open(path, "w") as f:
        f.write(header + body + "\n")

class TestPointCloudDedup:
    @pytest.fixture
    def checker(self):
        return PointCloudDedupChecker(voxel_size=0.1, chamfer_threshold=0.5)

    @pytest.fixture
    def sample_dir(self, tmp_path):
        d = tmp_path / "clouds"
        d.mkdir()
        pts = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
        _write_test_ply(str(d / "a.ply"), pts)
        _write_test_ply(str(d / "b.ply"), pts)
        return str(d)

    def test_empty_directory(self, checker, tmp_path):
        d = tmp_path / "empty_dir"
        d.mkdir()
        result = checker.check_directory(str(d))
        assert "error" in result

    def test_missing_directory(self, checker):
        result = checker.check_directory("/nonexistent/path")
        assert "error" in result

    def test_md5_exact_dedup(self, checker, sample_dir):
        result = checker.check_directory(sample_dir)
        assert result["total_files"] == 2
        assert result["exact_duplicates"] >= 1

    def test_find_near_duplicates_empty(self, checker):
        pairs = checker._find_near_duplicates([], {}, {})
        assert pairs == []

    def test_voxel_hash(self, checker, sample_dir):
        h = checker._voxel_hash(os.path.join(sample_dir, "a.ply"))
        assert h is not None
        assert isinstance(h, str)

    def test_voxel_hash_nonexistent(self, checker):
        h = checker._voxel_hash("/nonexistent.ply")
        assert h is None

    def test_md5_dedup(self, checker, sample_dir):
        files = [os.path.join(sample_dir, f) for f in ["a.ply", "b.ply"]]
        hashes, groups = checker._md5_dedup(files)
        assert len(groups) > 0

    def test_chamfer_identical(self, checker, sample_dir):
        a = os.path.join(sample_dir, "a.ply")
        b = os.path.join(sample_dir, "b.ply")
        d = checker._chamfer_distance(a, b)
        assert d is not None
        assert d < 1e-6

    def test_generate_report(self, checker):
        result = {
            "total_files": 10,
            "unique_files": 8,
            "exact_duplicates": 2,
            "near_duplicate_pairs": 1,
            "md5_groups": {"abc123": ["a.ply", "b.ply"]},
            "near_duplicates": [{"file_a": "a.ply", "file_b": "c.ply", "chamfer_distance": 0.001}],
        }
        report = checker.generate_report(result)
        assert "# Point Cloud Deduplication Report" in report
        assert "10" in report
        assert "abc123" in report

    def test_generate_report_save_to_file(self, checker, tmp_path):
        path = tmp_path / "dedup_report.md"
        checker.generate_report({"total_files": 1, "unique_files": 1, "exact_duplicates": 0,
                                  "near_duplicate_pairs": 0, "md5_groups": {}, "near_duplicates": []},
                                 output_path=str(path))
        assert path.exists()

    def test_chamfer_brute(self, checker):
        a = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        b = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        d = checker._chamfer_brute(a, b)
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_load_ply_ascii(self, checker, sample_dir):
        pts = checker._load_points(os.path.join(sample_dir, "a.ply"))
        assert pts is not None
        assert pts.shape == (3, 3)

    def test_load_points_unknown_format(self, checker, tmp_path):
        path = tmp_path / "test.xyz"
        np.savetxt(str(path), np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))
        pts = checker._load_points(str(path))
        assert pts is not None
        assert pts.shape == (2, 3)

    def test_load_points_nonexistent_file(self, checker):
        pts = checker._load_points("/none.ply")
        assert pts is None
