"""
LLM服务模块 - 大语言模型调用的高级封装。

提供对话、流式输出、缓存和token使用追踪等增强功能。
在基础适配器之上添加了缓存层和日志记录。
"""

import logging
from typing import Iterator

from src.llm.base_adapter import BaseLLMAdapter


class LLMService:
    """LLM服务 - 大语言模型调用的统一服务层。

    封装LLM适配器，提供缓存、日志记录和token统计功能。
    支持同步对话和流式输出两种模式。

    Attributes:
        _adapter: LLM适配器实例
        _cache: 可选的响应缓存
        _total_tokens: 累计token使用量估算
    """

    def __init__(self, adapter: BaseLLMAdapter, cache=None):
        """初始化LLM服务。

        Args:
            adapter: LLM适配器实例
            cache: 可选的响应缓存对象
        """
        self._adapter = adapter
        self._cache = cache
        self._logger = logging.getLogger("ResearchAgent.LLMService")
        self._total_tokens = 0

    @property
    def provider(self) -> str:
        """获取当前LLM提供商名称。"""
        return self._adapter.provider

    @property
    def total_tokens(self) -> int:
        """获取累计token使用量估算值。"""
        return self._total_tokens

    def chat(self, messages: list[dict], **kwargs) -> str:
        """同步对话 - 发送消息并获取LLM回复。

        支持缓存机制：先查缓存，命中则直接返回；未命中则调用LLM后缓存结果。

        Args:
            messages: 消息列表
            **kwargs: 传递给适配器的额外参数

        Returns:
            str: LLM的回复文本
        """
        # 检查缓存
        if self._cache:
            cached = self._cache.get(messages)
            if cached is not None:
                self._logger.info("LLM cache hit")
                return cached

        self._logger.info(f"Sending {len(messages)} messages to {self.provider}")
        response = self._adapter.chat(messages, **kwargs)
        self._total_tokens += self._estimate_tokens(str(messages), response)

        # 缓存结果
        if self._cache:
            self._cache.set(messages, response)

        self._logger.info(f"Response received, total tokens: {self._total_tokens}")
        return response

    def chat_stream(self, messages: list[dict], **kwargs) -> Iterator[str]:
        """流式对话 - 以流式方式逐步返回LLM生成的文本片段。

        Args:
            messages: 消息列表
            **kwargs: 传递给适配器的额外参数

        Yields:
            str: 逐步生成的文本片段
        """
        self._logger.info(f"Streaming {len(messages)} messages to {self.provider}")
        for chunk in self._adapter.chat_stream(messages, **kwargs):
            yield chunk

    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """简单估算token数量（基于单词数）。

        Args:
            prompt: 输入提示文本
            response: LLM响应文本

        Returns:
            int: 估算的token数量
        """
        return len(prompt.split()) + len(response.split())
