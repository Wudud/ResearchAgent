import logging
from pathlib import Path

from src.dataset.models import DatasetInventory, IntegrityIssue, IntegrityReport
from src.tools.filesystem.checksum import ChecksumTool

class IntegrityChecker:
    def __init__(self):
        self._checksum = ChecksumTool()
        self._logger = logging.getLogger("ResearchAgent.IntegrityChecker")

    def check(
        self, inventory: DatasetInventory, manifest_path: str = None
    ) -> IntegrityReport:
        report = IntegrityReport()
        scanned_paths = {f.relative_path for f in inventory.files}

        if manifest_path is None:
            manifest_path = Path(inventory.root_path) / "checksums.md5"

        manifest_path = Path(manifest_path)

        if not manifest_path.exists():
            self._logger.info(f"No checksum manifest found at {manifest_path}, skipping")
            return report

        self._logger.info(f"Checking integrity against: {manifest_path}")

        try:
            expected = self._checksum.load_manifest(str(manifest_path))
        except Exception as e:
            report.passed = False
            report.issues.append(
                IntegrityIssue(severity="error", file_path=str(manifest_path), message=str(e))
            )
            return report

        for rel_path, expected_hash in expected.items():
            if rel_path not in scanned_paths:
                report.missing_files.append(rel_path)
                report.passed = False
                continue

            entry = next(f for f in inventory.files if f.relative_path == rel_path)
            if entry.md5_hex != expected_hash:
                report.checksum_mismatches.append(rel_path)
                report.passed = False

        for rel_path in scanned_paths - set(expected.keys()):
            report.issues.append(
                IntegrityIssue(
                    severity="warning",
                    file_path=rel_path,
                    message="File not listed in manifest",
                )
            )

        self._logger.info(
            f"Integrity check: passed={report.passed}, "
            f"missing={len(report.missing_files)}, "
            f"mismatches={len(report.checksum_mismatches)}"
        )
        return report
