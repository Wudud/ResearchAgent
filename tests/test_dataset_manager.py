import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.dataset.scanner import DatasetScanner
from src.dataset.integrity import IntegrityChecker
from src.dataset.models import DatasetInventory, FileEntry
from src.dataset.statistics import StatisticsGenerator
from src.managers.dataset_manager import DatasetManager

def _make_sample_dataset(root: Path):
    """Create a minimal dataset with PLY and PCD files."""
    root.mkdir(parents=True, exist_ok=True)

    (root / "sample.ply").write_text("""ply
format ascii 1.0
element vertex 100
property float x
property float y
property float z
end_header""")
