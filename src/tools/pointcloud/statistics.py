from pathlib import Path

from src.tools.base_tool import BaseTool
from src.tools.pointcloud.ply_reader import PLYReader
from src.tools.pointcloud.pcd_reader import PCDReader

class PointCloudStatistics(BaseTool):
    @property
    def name(self) -> str:
        return "pointcloud_statistics"

    @property
    def description(self) -> str:
        return "Compute statistics (point count, file count) for point cloud files in a directory."

    def run(self, files: list[dict], **kwargs) -> dict:
        ply_files = [f for f in files if f["extension"] == ".ply"]
        pcd_files = [f for f in files if f["extension"] == ".pcd"]
        all_pc_files = ply_files + pcd_files

        if not all_pc_files:
            return {
                "total_pc_files": 0,
                "ply_files": 0,
                "pcd_files": 0,
                "min_points": None,
                "max_points": None,
                "avg_points": None,
            }

        ply_reader = PLYReader()
        pcd_reader = PCDReader()

        point_counts = []

        for f in ply_files:
            try:
                info = ply_reader.run(f["absolute_path"])
                if info["vertex_count"] > 0:
                    point_counts.append(info["vertex_count"])
            except ValueError:
                pass

        for f in pcd_files:
            try:
                info = pcd_reader.run(f["absolute_path"])
                if info["point_count"] > 0:
                    point_counts.append(info["point_count"])
            except ValueError:
                pass

        return {
            "total_pc_files": len(all_pc_files),
            "ply_files": len(ply_files),
            "pcd_files": len(pcd_files),
            "min_points": min(point_counts) if point_counts else None,
            "max_points": max(point_counts) if point_counts else None,
            "avg_points": round(sum(point_counts) / len(point_counts), 1) if point_counts else None,
        }
