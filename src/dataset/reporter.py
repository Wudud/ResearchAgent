import logging
from datetime import datetime

from src.dataset.models import DatasetInventory, DatasetStats, IntegrityReport
from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService

class ReportGenerator:
    def __init__(self, llm_service: LLMService, prompt_service: PromptService):
        self._llm = llm_service
        self._prompts = prompt_service
        self._logger = logging.getLogger("ResearchAgent.ReportGenerator")

    def generate(
        self,
        dataset_name: str,
        inventory: DatasetInventory,
        stats: DatasetStats,
        integrity: IntegrityReport,
    ) -> str:
        self._logger.info(f"Generating dataset report for: {dataset_name}")

        context = {
            "dataset_name": dataset_name,
            "root_path": inventory.root_path,
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": inventory.total_files,
            "total_size_human": stats.total_size_human,
            "extension_counts": self._format_dict(stats.extensions),
            "total_pc_files": stats.point_cloud_files,
            "min_points": stats.min_point_count or "N/A",
            "max_points": stats.max_point_count or "N/A",
            "avg_points": stats.avg_point_count or "N/A",
        }

        prompt = self._prompts.render("dataset/dataset_report.md", **context)
        messages = [
            {"role": "user", "content": prompt},
        ]

        if self._llm is None:
            raise RuntimeError("LLM service is not configured. Cannot generate report.")

        return self._llm.chat(messages)

    def _format_dict(self, d: dict) -> str:
        return ", ".join(f"{k}: {v}" for k, v in d.items())
