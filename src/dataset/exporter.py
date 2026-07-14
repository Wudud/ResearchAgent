import logging
from datetime import datetime
from pathlib import Path

from src.dataset.models import DatasetInventory, DatasetStats
from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService

class DatasetExporter:
    def __init__(self, llm_service: LLMService, prompt_service: PromptService):
        self._llm = llm_service
        self._prompts = prompt_service
        self._logger = logging.getLogger("ResearchAgent.DatasetExporter")

    def export_dataset_card(
        self,
        dataset_name: str,
        version: str,
        inventory: DatasetInventory,
        stats: DatasetStats,
    ) -> str:
        self._logger.info(f"Generating Dataset Card for: {dataset_name}")

        context = {
            "dataset_name": dataset_name,
            "version": version,
            "root_path": inventory.root_path,
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
            "total_files": inventory.total_files,
            "total_size_human": stats.total_size_human,
            "extension_counts": ", ".join(f"{k}: {v}" for k, v in stats.extensions.items()),
            "total_pc_files": stats.point_cloud_files,
            "ply_files": stats.ply_files,
            "pcd_files": stats.pcd_files,
            "min_points": stats.min_point_count or "N/A",
            "max_points": stats.max_point_count or "N/A",
            "avg_points": stats.avg_point_count or "N/A",
        }

        prompt = self._prompts.render("dataset/dataset_card.md", **context)
        messages = [
            {"role": "user", "content": prompt},
        ]

        if self._llm is None:
            raise RuntimeError("LLM service is not configured. Cannot export dataset card.")

        card_content = self._llm.chat(messages)
        return card_content

    def save_card(
        self,
        content: str,
        output_dir: str,
        filename: str = "DATASET_CARD.md",
    ) -> str:
        output_path = Path(output_dir) / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        self._logger.info(f"Dataset Card saved to: {output_path}")
        return str(output_path)
