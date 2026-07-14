from src.managers.base_manager import BaseManager
from src.dataset.scanner import DatasetScanner
from src.dataset.integrity import IntegrityChecker
from src.dataset.statistics import StatisticsGenerator
from src.dataset.reporter import ReportGenerator
from src.dataset.exporter import DatasetExporter
from src.dataset.models import DatasetInventory, IntegrityReport, DatasetStats

class DatasetManager(BaseManager):
    def __init__(self, agent=None):
        super().__init__("Dataset Manager", agent=agent)
        self._scanner: DatasetScanner | None = None
        self._integrity: IntegrityChecker | None = None
        self._statistics: StatisticsGenerator | None = None
        self._reporter: ReportGenerator | None = None
        self._exporter: DatasetExporter | None = None
        self._inventory: DatasetInventory | None = None
        self._stats: DatasetStats | None = None
        self._integrity_report: IntegrityReport | None = None

    def initialize(self):
        super().initialize()
        allowed_ext = (
            self.config.get("dataset.allowed_extensions")
            if self.config is not None
            else None
        )
        self._scanner = DatasetScanner(allowed_extensions=allowed_ext)
        self._integrity = IntegrityChecker()
        self._statistics = StatisticsGenerator()
        self._reporter = ReportGenerator(
            llm_service=self.services.get("llm") if self.services else None,
            prompt_service=self.services.get("prompt") if self.services else None,
        )
        self._exporter = DatasetExporter(
            llm_service=self.services.get("llm") if self.services else None,
            prompt_service=self.services.get("prompt") if self.services else None,
        )

    def scan_dataset(self, root_path: str = None) -> DatasetInventory:
        if root_path is None:
            root_path = self.config.get("dataset.root_dir", "./workspace/datasets")
        self._inventory = self._scanner.scan(root_path)
        if self.logger:
            self.logger.info(f"Dataset scanned: {self._inventory.total_files} files")
        return self._inventory

    def check_integrity(self, manifest_path: str = None) -> IntegrityReport:
        if self._inventory is None:
            raise RuntimeError("No dataset scanned. Call scan_dataset() first.")
        self._integrity_report = self._integrity.check(self._inventory, manifest_path)
        return self._integrity_report

    def get_statistics(self) -> DatasetStats:
        if self._inventory is None:
            raise RuntimeError("No dataset scanned. Call scan_dataset() first.")
        self._stats = self._statistics.generate(self._inventory)
        return self._stats

    def generate_report(self, dataset_name: str = None) -> str:
        if self._inventory is None:
            raise RuntimeError("No dataset scanned. Call scan_dataset() first.")
        if self._stats is None:
            self.get_statistics()
        if self._integrity_report is None:
            self.check_integrity()

        if dataset_name is None:
            dataset_name = self._inventory.root_path.rstrip("/").rstrip("\\").split("/")[-1]

        return self._reporter.generate(dataset_name, self._inventory, self._stats, self._integrity_report)

    def generate_dataset_card(self, dataset_name: str = None, version: str = "1.0.0") -> str:
        if self._inventory is None:
            raise RuntimeError("No dataset scanned. Call scan_dataset() first.")
        if self._stats is None:
            self.get_statistics()

        if dataset_name is None:
            dataset_name = self._inventory.root_path.rstrip("/").rstrip("\\").split("/")[-1]

        content = self._exporter.export_dataset_card(dataset_name, version, self._inventory, self._stats)
        output_path = self._exporter.save_card(content, self._inventory.root_path)
        return output_path

    @property
    def inventory(self) -> DatasetInventory | None:
        return self._inventory

    @property
    def statistics(self) -> DatasetStats | None:
        return self._stats

    @property
    def integrity_report(self) -> IntegrityReport | None:
        return self._integrity_report
