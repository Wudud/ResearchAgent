import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings

class Retriever:
    def __init__(self, persist_dir: str = "./workspace/chroma_db", cache=None):
        self._persist_dir = Path(persist_dir)
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._cache = cache
        self._logger = logging.getLogger("ResearchAgent.Retriever")

    def retrieve(
        self,
        query_embedding: list[float],
        collection_names: list[str] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """Search across collections. Returns list of {id, document, metadata, collection, distance}."""
        if collection_names is None:
            collection_names = self._client.list_collections()

        all_results = []
        for col_name in collection_names:
            try:
                collection = self._client.get_collection(col_name)
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, collection.count()),
                )
                if results["ids"] and results["ids"][0]:
                    for i, doc_id in enumerate(results["ids"][0]):
                        all_results.append({
                            "id": doc_id,
                            "document": results["documents"][0][i] if results["documents"] and results["documents"][0] else "",
                            "metadata": results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {},
                            "distance": results["distances"][0][i] if results["distances"] and results["distances"][0] else 0.0,
                            "collection": col_name,
                        })
            except Exception as e:
                self._logger.warning(f"Failed to query collection '{col_name}': {e}")

        all_results.sort(key=lambda x: x["distance"])
        return all_results[:top_k]
