"""
嵌入服务模块 - 嵌入功能的统一服务层。

支持批量嵌入、缓存和自动回退机制。
在基础适配器之上提供统一的文本向量化接口。
"""

import logging

from src.embedding.base_adapter import BaseEmbeddingAdapter


class EmbeddingService:
    """嵌入服务 - 文本向量化的统一服务入口。

    封装嵌入适配器，提供批量嵌入和缓存功能。
    支持在模型不可用时优雅降级。

    Attributes:
        _adapter: 嵌入适配器实例
        _cache: 可选的嵌入缓存
        _logger: 日志记录器
    """

    def __init__(self, adapter: BaseEmbeddingAdapter = None):
        """初始化嵌入服务。

        Args:
            adapter: 嵌入适配器实例，为None时服务不可用
        """
        self._adapter = adapter
        self._cache = None
        self._logger = logging.getLogger("ResearchAgent.EmbeddingService")

    @property
    def provider(self) -> str:
        """获取当前嵌入提供商名称。

        Returns:
            str: 提供商名称，适配器不可用时返回"none"
        """
        if self._adapter:
            return self._adapter.provider
        return "none"

    @property
    def available(self) -> bool:
        """检查嵌入服务是否可用。

        Returns:
            bool: 适配器存在且可用时返回True
        """
        return self._adapter is not None

    @property
    def dimension(self) -> int:
        """获取嵌入向量维度。

        Returns:
            int: 向量维度，不可用时返回0
        """
        if self._adapter:
            return getattr(self._adapter, 'dimension', 0)
        return 0

    def embed(self, text: str) -> list[float]:
        """对单个文本进行嵌入向量化。

        Args:
            text: 输入文本

        Returns:
            list[float]: 嵌入向量

        Raises:
            RuntimeError: 服务不可用时抛出
        """
        if not self.available:
            raise RuntimeError("Embedding service not available")

        if self._cache:
            cached = self._cache.get(text)
            if cached is not None:
                return cached

        result = self._adapter.embed(text)

        if self._cache and result:
            self._cache.set(text, result)

        return result

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量文本嵌入向量化。

        Args:
            texts: 输入文本列表

        Returns:
            list[list[float]]: 嵌入向量列表

        Raises:
            RuntimeError: 服务不可用时抛出
        """
        if not self.available:
            raise RuntimeError("Embedding service not available")

        if self._cache:
            return [self.embed(t) for t in texts]
        return self._adapter.embed_batch(texts)
