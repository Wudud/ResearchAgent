import json
import logging
from collections import Counter

class DatasetIntelligenceService:
    def __init__(self, llm_service=None):
        self._llm = llm_service
        self._logger = logging.getLogger("ResearchAgent.DatasetIntelligence")

    def analyze_statistics(self, inventory) -> dict:
        """Generate statistical distribution report from dataset inventory."""
        if inventory is None or inventory.total_files == 0:
            return {"error": "No data available"}

        ext_counts = inventory.extension_counts or {}
        total_size_mb = inventory.total_size_bytes / (1024 * 1024) if inventory.total_size_bytes else 0

        return {
            "total_files": inventory.total_files,
            "total_size_mb": round(total_size_mb, 2),
            "extension_distribution": ext_counts,
            "point_cloud_formats": {
                k: v for k, v in ext_counts.items()
                if k in [".ply", ".pcd", ".pts", ".xyz", ".xyzrgb", ".npy"]
            },
        }

    def generate_quality_report(self, inventory, stats=None, integrity=None) -> str:
        """Generate a Markdown quality report."""
        if self._llm:
            return self._generate_llm_report(inventory, stats, integrity)
        return self._generate_simple_report(inventory, stats, integrity)

    def _generate_llm_report(self, inventory, stats, integrity) -> str:
        data = {
            "total_files": inventory.total_files if inventory else 0,
            "total_size": f"{inventory.total_size_bytes / (1024**2):.2f} MB" if inventory else "0",
            "extensions": inventory.extension_counts if inventory else {},
            "point_cloud_files": stats.point_cloud_files if stats else 0,
            "min_points": stats.min_point_count if stats else None,
            "max_points": stats.max_point_count if stats else None,
            "avg_points": round(stats.avg_point_count, 1) if stats and stats.avg_point_count else None,
            "integrity_passed": integrity.passed if integrity else True,
        }

        prompt = f"""请基于以下数据集信息，生成一份数据集质量分析报告。

3. 针对 DairySheepHR 高质量可微增强数据集的标准提出评估

{json.dumps(data, ensure_ascii=False, indent=2)}"""
        if v1_inventory is None or v2_inventory is None:
            return "无法比较：数据集信息不完整。"

        added = v2_inventory.total_files - v1_inventory.total_files
        size_diff = (v2_inventory.total_size_bytes - v1_inventory.total_size_bytes) / (1024 * 1024)

        lines = ["# 数据集版本对比\n"]
        lines.append(f"## 文件数变化")
        lines.append(f"- v1: {v1_inventory.total_files} 个")
        lines.append(f"- v2: {v2_inventory.total_files} 个")
        lines.append(f"- 变化: {'+' if added >= 0 else ''}{added} 个")

        lines.append(f"\n## 大小变化")
        lines.append(f"- v1: {v1_inventory.total_size_bytes / (1024**2):.2f} MB")
        lines.append(f"- v2: {v2_inventory.total_size_bytes / (1024**2):.2f} MB")
        lines.append(f"- 变化: {'+' if size_diff >= 0 else ''}{size_diff:.2f} MB")

        # Format distribution changes
        new_exts = set(v2_inventory.extension_counts.keys()) - set(v1_inventory.extension_counts.keys())
        if new_exts:
            lines.append(f"\n## 新增格式")
            for ext in new_exts:
                lines.append(f"- {ext}: {v2_inventory.extension_counts[ext]} 个")

        return "\n".join(lines)
