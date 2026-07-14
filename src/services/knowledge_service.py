"""
知识库服务模块 - 知识检索的统一服务入口。

封装索引、检索和重排名的完整流水线。
提供文本索引、语义搜索和格式化引用功能。
"""

import logging

from src.knowledge.chunker import Chunker
from src.knowledge.indexer import Indexer
from src.knowledge.retriever import Retriever
from src.knowledge.citation import Citation
from src.knowledge.reranker import Reranker
from src.services.embedding_service import EmbeddingService


class KnowledgeService:
    """知识库服务 - 知识管理的统一入口。

    封装文档分块、向量索引、语义检索和结果重排名的完整流程。
    支持多来源类型的知识库管理。

    Attributes:
        _embedding: 嵌入服务
        _chunker: 文档分块器
        _indexer: 向量索引器
        _retriever: 语义检索器
        _reranker: 结果重排序器
        _citation: 引用格式化器
        _logger: 日志记录器
    """

    def __init__(self, embedding_service: EmbeddingService = None,
                 persist_dir: str = "./workspace/chroma_db",
                 reranker: Reranker = None):
        self._embedding = embedding_service
        self._chunker = Chunker()
        self._indexer = Indexer(persist_dir=persist_dir)
        self._retriever = Retriever(persist_dir=persist_dir)
        self._reranker = reranker
        self._citation = Citation()
        self._logger = logging.getLogger("ResearchAgent.KnowledgeService")

    @property
    def available(self) -> bool:
        """检查知识库服务是否可用。

        Returns:
            bool: 嵌入服务可用时返回True
        """
        return self._embedding is not None and self._embedding.available

    def index_text(self, source_type: str, text: str, metadata: dict = None) -> int:
        """将文本索引到知识库中。

        Args:
            source_type: 来源类型（如 "paper", "meeting", "experiment"）
            text: 要索引的文本内容
            metadata: 附加元数据

        Returns:
            int: 索引的文档块数量
        """
        if not self.available:
            self._logger.warning("Embedding not available, skipping index")
            return 0

        metadata = metadata or {}
        metadata["source_type"] = source_type

        chunks = self._chunker.chunk(text)
        if not chunks:
            return 0

        chunk_texts = [c["text"] for c in chunks]
        chunk_ids = [f"{source_type}_{metadata.get('id', 'doc')}_{c['index']}" for c in chunks]
        chunk_metadatas = [{**metadata, "chunk_index": c["index"]} for c in chunks]

        embeddings = self._embedding.embed_batch(chunk_texts)
        self._indexer.add(
            collection_name=source_type,
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=chunk_metadatas,
        )
        return len(chunks)

    def retrieve(self, query: str, source_types: list[str] = None, top_k: int = 5) -> list[dict]:
        """语义搜索知识库。

        Args:
            query: 查询文本
            source_types: 限定搜索的来源类型列表
            top_k: 返回结果数量

        Returns:
            list[dict]: 搜索结果列表，每项包含id、document、metadata、distance等字段
        """
        if not self.available:
            return []

        query_embedding = self._embedding.embed(query)
        collections = source_types if source_types else None
        results = self._retriever.retrieve(query_embedding, collection_names=collections, top_k=top_k)

        if self._reranker and self._reranker.available and results:
            results = self._reranker.rerank(query, results)

        return results

    def search(self, query: str, source_types: list[str] = None, top_k: int = 5) -> dict:
        """搜索并返回带格式化引用的结果。

        Args:
            query: 查询文本
            source_types: 来源类型过滤
            top_k: 返回数量

        Returns:
            dict: 包含results、citations和context的字典
        """
        results = self.retrieve(query, source_types=source_types, top_k=top_k)
        return {
            "results": results,
            "citations": self._citation.format_batch(results),
            "context": self._build_context(results),
        }

    def clear_source(self, source_type: str):
        """清除指定来源类型的所有索引。

        Args:
            source_type: 来源类型
        """
        self._indexer.delete_collection(source_type)

    def get_source_count(self, source_type: str) -> int:
        """获取指定来源类型的索引数量。

        Args:
            source_type: 来源类型

        Returns:
            int: 索引条目数
        """
        return self._indexer.collection_count(source_type)

    def _build_context(self, results: list[dict]) -> str:
        """将检索结果构建为LLM可用的上下文文本。

        Args:
            results: 检索结果列表

        Returns:
            str: 格式化的上下文文本
        """
        if not results:
            return ""
        parts = []
        for r in results:
            meta = r.get("metadata", {})
            title = meta.get("title", "Untitled")
            source_type = meta.get("source_type", "")
            parts.append(f"### [{source_type}] {title}\n{r.get('document', '')}")
        return "\n\n".join(parts)
