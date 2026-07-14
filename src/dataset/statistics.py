import logging
from pathlib import Path

from src.dataset.models import DatasetInventory, DatasetStats
from src.tools.pointcloud.statistics import PointCloudStatistics

class StatisticsGenerator:
    def __init__(self):
        self._pc_stats = PointCloudStatistics()
        self._logger = logging.getLogger("ResearchAgent.StatisticsGenerator")

    def generate(self, inventory: DatasetInventory) -> DatasetStats:
        self._logger.info("Generating statistics")

        size_mb = inventory.total_size_bytes / (1024 * 1024)
        if size_mb >= 1024:
            total_size_human = f"{size_mb / 1024:.2f} GB"
        else:
            total_size_human = f"{size_mb:.2f} MB"

        raw_files = [
            {
                "path": f.relative_path,
                "absolute_path": f.absolute_path,
                "size_bytes": f.size_bytes,
                "extension": f.extension,
            }
            for f in inventory.files
        ]

        pc_info = self._pc_stats.run(raw_files)

        root = Path(inventory.root_path)
        subdirs = self._list_subdirs(root)

        return DatasetStats(
            total_files=inventory.total_files,
            total_size_human=total_size_human,
            extensions=inventory.extension_counts,
            point_cloud_files=pc_info["total_pc_files"],
            ply_files=pc_info["ply_files"],
            pcd_files=pc_info["pcd_files"],
            avg_point_count=pc_info["avg_points"],
            min_point_count=pc_info["min_points"],
            max_point_count=pc_info["max_points"],
            subdirectories=subdirs,
        )

    def _list_subdirs(self, root: Path) -> list[str]:
        subdirs = []
        for entry in sorted(root.rglob("*")):
            if entry.is_dir():
                try:
                    entry.relative_to(root)
                    rel = str(entry.relative_to(root))
                    if rel != ".":
                        subdirs.append(rel)
                except ValueError:
                    pass
        return subdirs
