from src.managers.base_manager import BaseManager
from src.services.experiment_service import ExperimentService
from src.persistence.experiment_repository import ExperimentRepository

class ExperimentManager(BaseManager):
    def __init__(self, agent=None):
        super().__init__("Experiment Manager", agent=agent)
        self._service: ExperimentService | None = None

    def initialize(self):
        super().initialize()
        repo = None
        if self.services:
            repo = self.services.get("experiment_repo")
            if repo is None and self.config:
                db_path = self.config.get("chat.db_path", "./workspace/chat_history.db")
                repo = ExperimentRepository(db_path)

        self._service = ExperimentService(
            llm_service=self.services.get("llm") if self.services else None,
            prompt_service=self.services.get("prompt") if self.services else None,
            experiment_repo=repo,
        )

    @property
    def service(self) -> ExperimentService | None:
        return self._service

    def create_experiment(self, name: str, description: str = "", dataset: str = "",
                          model: str = "", parameters: dict = None,
                          log_path: str = "", checkpoint_path: str = "",
                          tensorboard_path: str = ""):
        return self._service.create_experiment(
            name, description, dataset, model, parameters,
            log_path, checkpoint_path, tensorboard_path)

    def log_parameters(self, exp_id: int, parameters: dict):
        self._service.log_parameters(exp_id, parameters)

    def log_metrics(self, exp_id: int, step: int = None, **metrics):
        self._service.log_metrics(exp_id, step, **metrics)

    def start_experiment(self, exp_id: int):
        self._service.start_experiment(exp_id)

    def complete_experiment(self, exp_id: int):
        self._service.complete_experiment(exp_id)

    def compare_experiments(self, exp_ids: list[int]) -> str:
        return self._service.compare_experiments(exp_ids)

    def generate_report(self, exp_id: int) -> str:
        return self._service.generate_report(exp_id)

    def get_experiment(self, exp_id: int):
        return self._service.get_experiment(exp_id)

    def list_experiments(self, status: str = None):
        return self._service.list_experiments(status)

    def delete_experiment(self, exp_id: int):
        self._service.delete_experiment(exp_id)
