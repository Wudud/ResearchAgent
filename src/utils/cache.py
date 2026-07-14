"""
缓存模块 - 提供嵌入缓存、LLM响应缓存和ChromaDB集合缓存

实现了三种缓存策略：
- EmbeddingCache: 基于LRU（最近最少使用）的文本→向量缓存
- LLMResponseCache: 基于TTL（生存时间）的对话响应缓存
- ChromaCollectionCache: ChromaDB集合句柄的定时刷新缓存
"""

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict


class EmbeddingCache:
    """文本→嵌入向量的LRU缓存。

    使用OrderedDict实现LRU淘汰策略，线程安全。
    避免对相同文本重复调用嵌入API，节省成本和时间。

    Attributes:
        _cache: 有序字典，key为文本MD5哈希，value为嵌入向量
        _maxsize: 最大缓存条目数
        _hits/_misses: 命中/未命中计数器
    """

    def __init__(self, maxsize: int = 1024):
        """初始化嵌入缓存。

        Args:
            maxsize: 最大缓存条目数，超出后淘汰最久未使用的条目
        """
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._logger = logging.getLogger("ResearchAgent.EmbeddingCache")

    def get(self, text: str) -> list[float] | None:
        """查找文本对应的缓存嵌入向量。

        Args:
            text: 输入文本

        Returns:
            缓存的嵌入向量，未命中时返回None
        """
        key = self._hash(text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)  # LRU: 将命中项移到末尾
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None

    def set(self, text: str, embedding: list[float]):
        """缓存文本的嵌入向量。

        Args:
            text: 原始文本
            embedding: 对应的嵌入向量
        """
        key = self._hash(text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = embedding
            # 超出容量时淘汰最久未使用的条目
            while len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def clear(self):
        """清空缓存并重置统计计数器。"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    @property
    def hit_rate(self) -> float:
        """缓存命中率。

        Returns:
            float: 命中次数 / 总请求次数，无请求时返回0.0
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @staticmethod
    def _hash(text: str) -> str:
        """计算文本的MD5哈希作为缓存键。

        Args:
            text: 输入文本

        Returns:
            str: MD5哈希的十六进制字符串
        """
        return hashlib.md5(text.encode("utf-8")).hexdigest()


class LLMResponseCache:
    """LLM对话响应的TTL缓存。

    按消息列表的哈希值缓存LLM响应，每个条目有生存时间限制。
    线程安全，自动淘汰过期条目。

    Attributes:
        _cache: key→(response, expiry_timestamp)的字典
        _ttl: 缓存条目的生存时间（秒）
        _maxsize: 最大缓存条目数
    """

    def __init__(self, ttl: int = 3600, maxsize: int = 512):
        """初始化LLM响应缓存。

        Args:
            ttl: 缓存生存时间（秒），默认3600秒（1小时）
            maxsize: 最大缓存条目数
        """
        self._cache: dict[str, tuple[str, float]] = {}  # key → (响应内容, 过期时间戳)
        self._ttl = ttl
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._logger = logging.getLogger("ResearchAgent.LLMResponseCache")

    def get(self, messages: list[dict]) -> str | None:
        """查找消息列表对应的缓存响应。

        Args:
            messages: LLM对话消息列表

        Returns:
            缓存的响应文本，未命中或已过期时返回None
        """
        key = self._hash(messages)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            response, expires = entry
            # 检查是否过期
            if time.time() > expires:
                del self._cache[key]
                self._misses += 1
                return None
            self._hits += 1
            return response

    def set(self, messages: list[dict], response: str):
        """缓存消息列表对应的LLM响应。

        Args:
            messages: LLM对话消息列表
            response: LLM返回的响应文本
        """
        key = self._hash(messages)
        with self._lock:
            self._cache[key] = (response, time.time() + self._ttl)
            # 超出容量时淘汰最早过期的条目
            while len(self._cache) > self._maxsize:
                oldest = min(self._cache.items(), key=lambda x: x[1][1])
                del self._cache[oldest[0]]

    def clear(self):
        """清空缓存并重置统计计数器。"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    @property
    def hit_rate(self) -> float:
        """缓存命中率。

        Returns:
            float: 命中次数 / 总请求次数
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @staticmethod
    def _hash(messages: list[dict]) -> str:
        """计算消息列表的MD5哈希作为缓存键。

        Args:
            messages: LLM消息列表

        Returns:
            str: MD5哈希的十六进制字符串
        """
        raw = json.dumps(messages, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()


class ChromaCollectionCache:
    """ChromaDB集合句柄缓存 - 避免重复获取集合引用。

    每个集合句柄有TTL限制，超时后自动失效。
    用于减少ChromaDB的集合查找操作。

    Attributes:
        _collections: 集合名→(collection对象, 过期时间戳)的字典
        _ttl: 缓存生存时间（秒）
    """

    def __init__(self, ttl: int = 300):
        """初始化ChromaDB集合缓存。

        Args:
            ttl: 缓存生存时间（秒），默认300秒（5分钟）
        """
        self._collections: dict[str, tuple[object, float]] = {}  # 名称 → (集合对象, 过期时间戳)
        self._ttl = ttl
        self._lock = threading.Lock()
        self._logger = logging.getLogger("ResearchAgent.ChromaCollectionCache")

    def get(self, name: str) -> object | None:
        """获取指定名称的缓存集合句柄。

        Args:
            name: 集合名称

        Returns:
            缓存的集合对象，不存在或已过期时返回None
        """
        with self._lock:
            entry = self._collections.get(name)
            if entry is None:
                return None
            col, expires = entry
            # 检查是否过期
            if time.time() > expires:
                del self._collections[name]
                return None
            return col

    def set(self, name: str, collection: object):
        """缓存集合句柄。

        Args:
            name: 集合名称
            collection: ChromaDB集合对象
        """
        with self._lock:
            self._collections[name] = (collection, time.time() + self._ttl)

    def invalidate(self, name: str):
        """使指定集合的缓存失效。

        Args:
            name: 要失效的集合名称
        """
        with self._lock:
            self._collections.pop(name, None)

    def clear(self):
        """清空所有缓存的集合句柄。"""
        with self._lock:
            self._collections.clear()
