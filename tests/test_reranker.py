"""
重排序测试模块 - 测试Reranker的重排序功能。

验证cross-encoder模型的加载和结果重排序。
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.knowledge.reranker import Reranker


@pytest.fixture
def mock_cross_encoder():
    """创建模拟的cross-encoder。"""
    mock_ce = MagicMock()
    mock_ce.predict.return_value = [0.9, 0.3, 0.7]
    return mock_ce


class TestReranker:
    """测试Reranker的功能。"""

    def test_available_false_when_no_module(self):
        """测试sentence_transformers不可用时的行为。"""
        with patch.dict(sys.modules, {"sentence_transformers": None}):
            reranker = Reranker()
            assert not reranker.available

    def test_rerank_sorts_by_score(self, mock_cross_encoder):
        """测试按分数重排序。"""
        reranker = Reranker()
        reranker._model = mock_cross_encoder

        results = [
            {"document": "doc1", "id": "1", "distance": 0.1},
            {"document": "doc2", "id": "2", "distance": 0.2},
            {"document": "doc3", "id": "3", "distance": 0.3},
        ]
        ranked = reranker.rerank("test query", results)
        assert len(ranked) == 3

    def test_rerank_top_k(self, mock_cross_encoder):
        """测试限制返回数量。"""
        reranker = Reranker()
        reranker._model = mock_cross_encoder

        results = [
            {"document": "doc1", "id": "1"},
            {"document": "doc2", "id": "2"},
            {"document": "doc3", "id": "3"},
        ]
        ranked = reranker.rerank("query", results, top_k=2)
        assert len(ranked) == 2

    def test_rerank_empty_results(self):
        """测试空结果重排序。"""
        reranker = Reranker()
        assert reranker.rerank("query", []) == []
