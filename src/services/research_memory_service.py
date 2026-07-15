import logging

from src.persistence.memory_repository import ResearchMemory, ResearchMemoryRepository

class ResearchMemoryService:
    def __init__(self, memory_repo: ResearchMemoryRepository = None, semantic_store=None):
        self._repo = memory_repo
        self._semantic = semantic_store
        self._logger = logging.getLogger("ResearchAgent.ResearchMemoryService")

    def get_memory(self, memory_id: str) -> ResearchMemory | None:
        return self._repo.get(memory_id)

    def list_by_category(self, category: str = None):
        return self._repo.list_by_category(category)

    def search(self, keyword: str):
        """Fused search: SQLite full-text + semantic vector search."""
        db_results = self._repo.search(keyword)
        semantic_items = []
        if self._semantic and self._semantic.available:
            try:
                semantic_items = self._semantic.query(keyword, top_k=5)
            except Exception as e:
                self._logger.warning(f"Semantic search failed: {e}")

        # Merge: pull matching SemanticMemory items into ResearchMemory
        merged = {m.id: m for m in db_results}
        for item in semantic_items:
            meta = item.get("metadata", {})
            rid = meta.get("research_memory_id")
            if rid and rid not in merged:
                from src.persistence.memory_repository import ResearchMemory
                rm = ResearchMemory(
                    id=rid,
                    category=meta.get("category", ""),
                    title=meta.get("title", ""),
                    content=item.get("value", ""),
                    source=meta.get("source", ""),
                )
                merged[rid] = rm

        return list(merged.values())

    def delete_memory(self, memory_id: str):
        self._repo.delete(memory_id)

    def get_relevant_context(self, query: str, max_results: int = 5) -> str:
        results = self.search(query)
        if not results:
            return ""

        items = results[:max_results]
        return "\n\n".join(f"[{m.category}] {m.title}: {m.content}" for m in items)
