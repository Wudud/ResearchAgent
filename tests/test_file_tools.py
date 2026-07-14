import os
import tempfile
from pathlib import Path

import pytest

from src.tools.filesystem.scanner import FileScanner
from src.tools.filesystem.checksum import ChecksumTool

class TestFileScanner:
    def test_scanner_lists_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.ply").write_text("test")
            Path(tmpdir, "b.ply").write_text("test")
            Path(tmpdir, "sub").mkdir()
            Path(tmpdir, "sub", "c.ply").write_text("test")

            scanner = FileScanner()
            results = scanner.run(root_path=tmpdir, allowed_extensions=[".ply"])

            assert len(results) == 3
            paths = sorted([r["path"] for r in results])
            assert "a.ply" in paths
            assert any(p.replace("\\", "/") == "sub/c.ply" for p in paths)

    def test_scanner_filters_extensions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.ply").write_text("test")
            Path(tmpdir, "b.txt").write_text("test")
            Path(tmpdir, "c.pcd").write_text("test")

            scanner = FileScanner()
            results = scanner.run(root_path=tmpdir, allowed_extensions=[".ply"])

            assert len(results) == 1
            assert results[0]["extension"] == ".ply"

    def test_scanner_nonexistent_directory(self):
        scanner = FileScanner()
        with pytest.raises(FileNotFoundError):
            scanner.run(root_path="/nonexistent/path")

class TestChecksumTool:
    def test_compute_md5(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("hello world")
            f.flush()

        try:
            tool = ChecksumTool()
            result = tool.run(f.name, algorithm="md5")
            assert len(result) == 32
            assert result == "5eb63bbbe01eeed093cb22bb8f5acdc3"
        finally:
            os.unlink(f.name)

    def test_verify_correct_hash(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("hello world")
            f.flush()

        try:
            tool = ChecksumTool()
            assert tool.verify(f.name, "5eb63bbbe01eeed093cb22bb8f5acdc3")
            assert not tool.verify(f.name, "00000000000000000000000000000000")
        finally:
            os.unlink(f.name)

    def test_load_manifest(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md5", delete=False) as f:
            f.write("abc123  file1.ply\n")
            f.write("def456  sub/file2.ply\n")
            f.write("# comment line\n")
            f.flush()

        try:
            tool = ChecksumTool()
            entries = tool.load_manifest(f.name)
            assert entries == {"file1.ply": "abc123", "sub/file2.ply": "def456"}
        finally:
            os.unlink(f.name)

    def test_checksum_nonexistent_file(self):
        tool = ChecksumTool()
        with pytest.raises(FileNotFoundError):
            tool.run("/nonexistent/file.ply")
