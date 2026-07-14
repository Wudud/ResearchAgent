"""
语义记忆存储模块 - 基于向量相似度的长期记忆系统。

自动存储和检索与当前上下文相关的历史经验。
使用ChromaDB作为向量存储后端，支持持久化和语义搜索。
"""

import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings


class SemanticMemoryStore:
    """语义记忆存储 - 基于向量数据库的经验记忆系统。

    使用ChromaDB存储经验文本的嵌入向量，
    支持按语义相似度检索相关历史经验。

    Attributes:
        _embedding_service: 嵌入服务
        _persist_dir: 持久化目录
        _client: ChromaDB客户端
        _collection: 记忆集合
    """

    def __init__(self, embedding_service, persist_dir: str = "./workspace/chroma_db"):
        self._embedding = embedding_service
        self._persist_dir = persist_dir
        self._logger = logging.getLogger("ResearchAgent.SemanticMemoryStore")

        if persist_dir == ":memory:":
            self._client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            Path(persist_dir).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        self._collection = self._client.get_or_create_collection("research_memory")

    def save(self, key: str, value: str):
        """保存键值对（别名）。"""
        self.add(value, {"key": key}, doc_id=key)

    @property
    def available(self) -> bool:
        return self._embedding is not None and self._embedding.available

    def add(self, text: str, metadata: dict = None, doc_id: str = None):
        """添加记忆条目。

        Args:
            text: 记忆文本
            metadata: 附加元数据
            doc_id: 文档ID（自动生成如果未提供）
        """
        if not self._embedding or not self._embedding.available:
            self._logger.warning("Embedding not available, cannot add memory")
            return

        embedding = self._embedding.embed(text)
        doc_id = doc_id or str(hash(text))
        self._collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}],
        )

    def search(self, query: str, top_k: int = 5) -> list:
        """按语义相似度搜索相关记忆。

        Args:
            query: 查询文本
            top_k: 返回的最大结果数

        Returns:
            list: 搜索结果列表
        """
        if not self._embedding or not self._embedding.available:
            return []

        query_embedding = self._embedding.embed(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        return self._format_results(results)

    def _format_results(self, results: dict) -> list:
        """格式化ChromaDB查询结果。

        Args:
            results: ChromaDB原始查询结果

        Returns:
            list: 格式化后的结果列表
        """
        formatted = []
        if not results.get("ids") or not results["ids"][0]:
            return formatted

        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i] if results.get("documents") else "",
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
            })
        return formatted

    def query(self, query: str, top_k: int = 5) -> list[dict]:
        """查询相关记忆（别名）。"""
        return self.search(query, top_k=top_k)

    def clear(self):
        """清空所有记忆。"""
        self._client.delete_collection("research_memory")
        self._collection = self._client.get_or_create_collection("research_memory")
