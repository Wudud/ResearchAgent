import logging

class MemoryService:
    def __init__(self, semantic_store=None):
        self._store: dict[str, str] = {}
        self._semantic = semantic_store
        self._logger = logging.getLogger("ResearchAgent.MemoryService")

    def save(self, key: str, value: str):
        self._store[key] = value
        if self._semantic:
            self._semantic.save(key, value)
        self._logger.info(f"Memory saved: {key}")

    def load(self, key: str) -> str | None:
        return self._store.get(key)

    def query(self, query: str) -> list[str]:
        if self._semantic and self._semantic.available:
            results = self._semantic.query(query)
            return [r["value"] for r in results if r.get("value")]

        # Fallback: substring matching
        results = []
        for key, value in self._store.items():
            if query.lower() in key.lower() or query.lower() in value.lower():
                results.append(value)
        return results

    def semantic_search(self, query: str, top_k: int = 5) -> list[dict]:
        """Rich semantic search returning full result dicts."""
        if self._semantic:
            return self._semantic.query(query, top_k=top_k)
        return [{"key": k, "value": v, "metadata": {}} for k, v in self._store.items()
                if query.lower() in k.lower() or query.lower() in v.lower()][:top_k]

    def clear(self):
        self._store.clear()
        if self._semantic:
            self._semantic.clear()
        self._logger.info("Memory cleared")

    # --- 旧API别名 ---
    def add_memory(self, category: str, title: str, content: str, source: str = ""):
        self.save(f"{category}:{title}", content)

    def search(self, query: str):
        return self.query(query)

    def clear_all(self):
        self.clear()
