"""
缓存测试模块 - 测试EmbeddingCache、LLMResponseCache和ChromaCollectionCache。

测试覆盖缓存的命中、未命中、TTL过期和LRU淘汰等行为。
"""

import time

import pytest

from src.utils.cache import EmbeddingCache, LLMResponseCache, ChromaCollectionCache


class TestEmbeddingCache:
    """测试嵌入向量缓存（EmbeddingCache）。

    验证LRU淘汰策略、命中率计算和缓存清空功能。
    """

    @pytest.fixture
    def cache(self):
        """创建容量为3的EmbeddingCache实例。"""
        return EmbeddingCache(maxsize=3)

    def test_get_miss_returns_none(self, cache):
        """测试未命中时返回None。"""
        assert cache.get("unknown") is None

    def test_set_and_get(self, cache):
        """测试基本写入和读取。"""
        emb = [0.1, 0.2, 0.3]
        cache.set("hello", emb)
        assert cache.get("hello") == emb

    def test_lru_eviction(self, cache):
        """测试LRU淘汰策略：最久未使用的条目被淘汰。"""
        for i in range(5):
            cache.set(str(i), [float(i)])
        assert cache.get("0") is None  # 最先插入的最先被淘汰
        assert cache.get("1") is None
        assert cache.get("2") is not None
        assert cache.get("4") is not None

    def test_lru_access_reorders(self, cache):
        """测试访问操作会更新LRU顺序。"""
        for i in range(3):
            cache.set(str(i), [float(i)])
        cache.get("0")  # 访问"0"使其变为最近使用
        cache.set("3", [3.0])
        assert cache.get("1") is None  # "1"未被访问，被淘汰
        assert cache.get("0") is not None  # "0"被访问过，保留

    def test_hit_rate(self, cache):
        """测试缓存命中率计算。"""
        cache.set("a", [1.0])
        cache.get("a")  # 命中
        cache.get("b")  # 未命中
        assert cache.hit_rate == 0.5

    def test_clear(self, cache):
        """测试清空缓存并重置统计。"""
        cache.set("a", [1.0])
        cache.clear()
        assert cache.get("a") is None
        assert cache.hit_rate == 0.0


class TestLLMResponseCache:
    """测试LLM响应缓存（LLMResponseCache）。

    验证TTL过期机制、最大容量限制和命中率统计。
    """

    @pytest.fixture
    def cache(self):
        """创建TTL为60秒、最大容量为3的LLMResponseCache实例。"""
        return LLMResponseCache(ttl=60, maxsize=3)

    def test_miss_returns_none(self, cache):
        """测试未命中时返回None。"""
        assert cache.get([{"role": "user", "content": "hi"}]) is None

    def test_set_and_get(self, cache):
        """测试基本写入和读取。"""
        msgs = [{"role": "user", "content": "hi"}]
        cache.set(msgs, "hello")
        assert cache.get(msgs) == "hello"

    def test_ttl_expiry(self):
        """测试TTL过期后缓存条目不可用。"""
        cache = LLMResponseCache(ttl=0)  # TTL为0，立即过期
        msgs = [{"role": "user", "content": "hi"}]
        cache.set(msgs, "hello")
        time.sleep(0.01)
        assert cache.get(msgs) is None

    def test_hit_rate(self, cache):
        """测试命中率计算。"""
        msgs = [{"role": "user", "content": "a"}]
        cache.set(msgs, "resp")
        cache.get(msgs)  # 命中
        cache.get([{"role": "user", "content": "b"}])  # 未命中
        assert cache.hit_rate == 0.5

    def test_clear(self, cache):
        """测试清空缓存。"""
        msgs = [{"role": "user", "content": "hi"}]
        cache.set(msgs, "hello")
        cache.clear()
        assert cache.get(msgs) is None


class TestChromaCollectionCache:
    """测试ChromaDB集合缓存（ChromaCollectionCache）。

    验证TTL过期、失效操作和清空功能。
    """

    @pytest.fixture
    def cache(self):
        """创建TTL为60秒的ChromaCollectionCache实例。"""
        return ChromaCollectionCache(ttl=60)

    def test_miss_returns_none(self, cache):
        """测试未命中时返回None。"""
        assert cache.get("missing") is None

    def test_set_and_get(self, cache):
        """测试基本写入和读取。"""
        col = object()
        cache.set("test_col", col)
        assert cache.get("test_col") is col

    def test_ttl_expiry(self):
        """测试TTL过期后缓存条目不可用。"""
        cache = ChromaCollectionCache(ttl=0)  # TTL为0，立即过期
        cache.set("test", object())
        time.sleep(0.01)
        assert cache.get("test") is None

    def test_invalidate(self, cache):
        """测试主动失效操作。"""
        cache.set("test", object())
        cache.invalidate("test")
        assert cache.get("test") is None

    def test_clear(self, cache):
        """测试清空所有缓存条目。"""
        cache.set("a", object())
        cache.set("b", object())
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
