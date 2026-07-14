"""
LLM适配器工厂 - 根据配置创建对应的LLM适配器实例

支持OpenAI和DeepSeek提供商（两者都兼容OpenAI API协议），
通过配置文件中的default_provider决定使用哪个提供商。
"""

from src.llm.base_adapter import BaseLLMAdapter
from src.llm.openai_adapter import OpenAIAdapter


def create_llm_adapter(config) -> BaseLLMAdapter:
    """根据配置创建LLM适配器实例。

    从配置文件读取默认提供商和相关参数，
    支持openai和deepseek两种提供商。

    Args:
        config: ConfigManager实例

    Returns:
        BaseLLMAdapter: 对应提供商的适配器实例

    Raises:
        ValueError: 提供商配置不存在或提供商类型未知时抛出
    """
    provider = config.get("llm.default_provider", "openai")
    provider_config = config.get(f"llm.providers.{provider}")

    if provider_config is None:
        raise ValueError(f"LLM provider '{provider}' not found in config")

    # OpenAI和DeepSeek使用相同的适配器（兼容OpenAI API协议）
    if provider in ("openai", "deepseek"):
        return OpenAIAdapter(
            api_key=provider_config["api_key"],
            base_url=provider_config.get("base_url", "https://api.openai.com/v1"),
            model=provider_config["model"],
            temperature=provider_config.get("temperature", 0.3),
            max_tokens=provider_config.get("max_tokens", 4096),
        )

    raise ValueError(f"Unknown LLM provider: {provider}")
