from src.managers.base_manager import BaseManager
from src.services.paper_service import PaperService
from src.persistence.paper_repository import PaperRepository

class PaperManager(BaseManager):
    def __init__(self, agent=None):
        super().__init__("Paper Manager", agent=agent)
        self._service: PaperService | None = None

    def initialize(self):
        super().initialize()
        repo = None
        if self.services:
            repo = self.services.get("paper_repo")
            if repo is None and self.config:
                db_path = self.config.get("chat.db_path", "./workspace/chat_history.db")
                repo = PaperRepository(db_path)

        self._service = PaperService(
            llm_service=self.services.get("llm") if self.services else None,
            prompt_service=self.services.get("prompt") if self.services else None,
            paper_repo=repo,
            knowledge_service=self.services.get("knowledge_service") if self.services else None,
        )

    @property
    def service(self) -> PaperService | None:
        return self._service

    def process_paper(self, file_path: str):
        return self._service.process_paper(file_path)

    def get_paper(self, paper_id: str):
        return self._service.get_paper(paper_id)

    def list_papers(self):
        return self._service.list_papers()

    def search_paper(self, keyword: str):
        return self._service.search_paper(keyword)

    def delete_paper(self, paper_id: str):
        self._service.delete_paper(paper_id)
