"""
重排序模块 - 对初步检索结果进行二次排序。

使用cross-encoder模型提高检索结果的相关性。
通过语义相似度评分对初步检索结果进行精细化重排。
"""

import logging


class Reranker:
    """重排序器 - 使用cross-encoder提升检索质量。

    对Retriever返回的初步结果进行语义级别的重新评分和排序。

    Attributes:
        model_name: cross-encoder模型名称
        _model: 加载的模型实例（延迟加载）
        _logger: 日志记录器
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None
        self._logger = logging.getLogger("ResearchAgent.Reranker")

    @property
    def available(self) -> bool:
        """检查重排序器是否可用。

        Returns:
            bool: 模型加载成功返回True
        """
        try:
            if self._model is None:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            return True
        except Exception as e:
            self._logger.warning(f"Reranker not available: {e}")
            return False

    def rerank(self, query: str, results: list[dict], top_k: int = None) -> list[dict]:
        """对检索结果进行重排序。

        Args:
            query: 原始查询文本
            results: 初步检索结果列表
            top_k: 返回的最大结果数（None则返回全部）

        Returns:
            list[dict]: 重排序后的结果列表
        """
        if not self.available or not results:
            return results[:top_k] if top_k else results

        try:
            pairs = []
            for r in results:
                doc = r.get("document", "")
                pairs.append([query, doc])

            scores = self._model.predict(pairs)

            for i, r in enumerate(results):
                r["rerank_score"] = float(scores[i]) if hasattr(scores, '__iter__') else float(scores)

            results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

            return results[:top_k] if top_k else results
        except Exception as e:
            self._logger.warning(f"Reranking failed: {e}")
            return results[:top_k] if top_k else results
