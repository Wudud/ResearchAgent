"""
OpenAI适配器 - 封装OpenAI API兼容的LLM调用

支持所有兼容OpenAI API协议的提供商（如OpenAI官方API、DeepSeek API等），
提供同步和流式两种聊天模式。
"""

from typing import Iterator

import openai

from src.llm.base_adapter import BaseLLMAdapter
from src.utils.exceptions import LLMError


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI API兼容适配器 - 支持OpenAI官方API和DeepSeek等兼容API。

    封装了OpenAI Python SDK的调用细节，统一处理异常和参数配置。

    Attributes:
        _api_key: API密钥
        _base_url: API基础URL
        _model: 模型名称
        _temperature: 默认温度参数（控制输出随机性）
        _max_tokens: 默认最大输出token数
        _client: OpenAI客户端实例
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        """初始化OpenAI适配器。

        Args:
            api_key: API密钥
            base_url: API基础URL，默认OpenAI官方地址
            model: 使用的模型名称
            temperature: 温度参数（0-2），越低输出越确定
            max_tokens: 单次回复最大token数
        """
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)

    @property
    def provider(self) -> str:
        """返回提供商名称。

        Returns:
            str: "openai"
        """
        return "openai"

    def chat(self, messages: list[dict], **kwargs) -> str:
        """同步聊天 - 发送消息并等待完整回复。

        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "..."}, ...]
            **kwargs: 可覆盖默认参数（temperature, max_tokens等）

        Returns:
            str: LLM的完整回复文本

        Raises:
            LLMError: API调用失败时抛出
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_tokens", self._max_tokens),
            )
            return response.choices[0].message.content or ""
        except openai.OpenAIError as e:
            raise LLMError(str(e)) from e

    def chat_stream(self, messages: list[dict], **kwargs) -> Iterator[str]:
        """流式聊天 - 以流式方式逐步返回回复内容。

        Args:
            messages: 消息列表
            **kwargs: 可覆盖默认参数

        Yields:
            str: 实时生成的文本片段

        Raises:
            LLMError: API调用失败时抛出
        """
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_tokens", self._max_tokens),
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except openai.OpenAIError as e:
            raise LLMError(str(e)) from e
