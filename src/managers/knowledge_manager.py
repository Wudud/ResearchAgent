from src.managers.base_manager import BaseManager
from src.services.knowledge_service import KnowledgeService

class KnowledgeManager(BaseManager):
    def __init__(self, agent=None):
        super().__init__("Knowledge Manager", agent=agent)
        self._service: KnowledgeService | None = None

    def initialize(self):
        super().initialize()
        # Use the shared KnowledgeService from agent services
        self._service = self.services.get("knowledge_service") if self.services else None
        if self._service is None:
            persist_dir = "./workspace/chroma_db"
            if self.config:
                persist_dir = self.config.get("knowledge.persist_dir", "./workspace/chroma_db")
            self._service = KnowledgeService(
                embedding_service=self.services.get("embedding") if self.services else None,
                persist_dir=persist_dir,
            )

    @property
    def service(self) -> KnowledgeService | None:
        return self._service

    def index_paper(self, paper) -> int:
        """Index a paper into the knowledge base."""
        if paper.summary is None:
            return 0
        metadata = {
            "id": paper.id or "",
            "authors": paper.authors or "",
            "keywords": ", ".join(paper.keywords) if paper.keywords else "",
        }
        return self._service.index_text("paper", text, metadata)

    def index_meeting(self, meeting) -> int:
        """Index a meeting into the knowledge base."""
        metadata = {
            "id": meeting.id or "",
            "date": meeting.created_at or "",
        }
        return self._service.index_text("meeting", text, metadata)

    def index_experiment(self, exp) -> int:
        """Index an experiment into the knowledge base."""
        metadata = {
            "id": str(exp.id or ""),
            "dataset": exp.dataset or "",
            "model": exp.model or "",
            "status": exp.status or "",
        }
        return self._service.index_text("experiment", text, metadata)

    def index_dataset_info(self, dataset_name: str, dataset_card: str, metadata: dict = None) -> int:
        """Index dataset card/documentation into the knowledge base."""
        meta = {"title": dataset_name, **(metadata or {})}
        return self._service.index_text("dataset", text, meta)

    def index_document(self, title: str, content: str, metadata: dict = None) -> int:
        """Index a generic document into the knowledge base."""
        meta = {"title": title, **(metadata or {})}
        return self._service.index_text("document", title + "\n" + content, meta)

    def search(self, query: str, source_types: list[str] = None, top_k: int = 5) -> dict:
        return self._service.search(query, source_types=source_types, top_k=top_k)

    def retrieve(self, query: str, source_types: list[str] = None, top_k: int = 5) -> list[dict]:
        return self._service.retrieve(query, source_types=source_types, top_k=top_k)

    def clear_source(self, source_type: str):
        self._service.clear_source(source_type)

    def get_stats(self) -> dict:
        sources = ["paper", "meeting", "research_memory", "dataset", "experiment", "document"]
        return {s: self._service.get_source_count(s) for s in sources}
