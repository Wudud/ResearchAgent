import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings

class Indexer:
    def __init__(self, persist_dir: str = "./workspace/chroma_db", cache=None):
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._cache = cache
        self._logger = logging.getLogger("ResearchAgent.Indexer")

    def get_or_create_collection(self, name: str) -> "chromadb.Collection":
        if self._cache:
            cached = self._cache.get(name)
            if cached is not None:
                return cached
        collection = self._client.get_or_create_collection(name=name)
        if self._cache:
            self._cache.set(name, collection)
        return collection

    def add(
        self,
        collection_name: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] = None,
    ):
        collection = self.get_or_create_collection(collection_name)
        if metadatas is None:
            metadatas = [{}] * len(ids)
        collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        self._logger.info(f"Added {len(ids)} chunks to collection '{collection_name}'")

    def delete_collection(self, name: str):
        try:
            self._client.delete_collection(name)
            self._logger.info(f"Deleted collection: {name}")
        except Exception:
            pass

    def collection_count(self, name: str) -> int:
        try:
            collection = self._client.get_collection(name)
            return collection.count()
        except Exception:
            return 0

    def list_collections(self) -> list[str]:
        return self._client.list_collections()
