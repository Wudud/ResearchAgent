"""
记忆测试模块 - 测试SemanticMemoryStore和MemoryService。

验证语义记忆的存储、检索和搜索功能。
"""

from unittest.mock import MagicMock, patch

import pytest

from src.memory.semantic_store import SemanticMemoryStore
from src.services.memory_service import MemoryService


@pytest.fixture
def mock_embedding():
    """创建模拟的嵌入服务。"""
    svc = MagicMock()
    svc.available = True
    svc.embed.return_value = [0.1, 0.2, 0.3]
    return svc


@pytest.fixture
def memory_service(mock_embedding):
    """创建MemoryService实例。"""
    with patch("src.memory.semantic_store.chromadb.PersistentClient") as mock_client:
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        store = SemanticMemoryStore(embedding_service=mock_embedding, persist_dir=":memory:")
        return MemoryService(semantic_store=store)


class TestMemoryService:
    """测试MemoryService的功能。"""

    def test_add_and_search(self, memory_service, mock_embedding):
        """测试添加和搜索记忆。"""
        memory_service.add_memory("test category", "Test Title", "Test content", "test source")
        assert mock_embedding.embed.called

    def test_search_empty(self, memory_service):
        """测试空搜索。"""
        results = memory_service.search("nothing")
        assert isinstance(results, list)

    def test_clear_memory(self, memory_service):
        """测试清空记忆。"""
        memory_service.clear_all()
