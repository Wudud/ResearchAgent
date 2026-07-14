"""
LLM适配器基类 - 定义大语言模型适配器的抽象接口

所有LLM适配器（OpenAI、DeepSeek等）都必须实现此接口，
确保系统可以无缝切换不同的LLM提供商。
"""

from abc import ABC, abstractmethod
from typing import Iterator


class BaseLLMAdapter(ABC):
    """LLM适配器抽象基类 - 定义统一的聊天接口。

    所有LLM提供商的具体适配器都必须继承此类，
    实现chat、chat_stream和provider三个接口。
    """

    @abstractmethod
    def chat(self, messages: list[dict], **kwargs) -> str:
        """同步聊天接口 - 发送消息并获取完整回复。

        Args:
            messages: 消息列表，每条消息包含role和content
            **kwargs: 额外参数（可覆盖默认temperature、max_tokens等）

        Returns:
            str: LLM的完整回复文本
        """
        ...

    @abstractmethod
    def chat_stream(self, messages: list[dict], **kwargs) -> Iterator[str]:
        """流式聊天接口 - 以流式方式逐块返回回复内容。

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            str: 逐步生成的回复文本片段
        """
        ...

    @property
    @abstractmethod
    def provider(self) -> str:
        """返回LLM提供商名称标识。

        Returns:
            str: 提供商名称（如 "openai", "deepseek"）
        """
        ...
