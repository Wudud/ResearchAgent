from src.vision.vision_adapter import BaseVisionAdapter
from src.vision.openai_vision_adapter import OpenAIVisionAdapter


def create_vision_adapter(config) -> BaseVisionAdapter | None:
    provider = config.get("vision.default_provider")
    if provider is None:
        return None

    provider_config = config.get(f"vision.providers.{provider}")
    if provider_config is None:
        raise ValueError(f"Vision provider '{provider}' not found in config")

    if provider == "openai":
        return OpenAIVisionAdapter(
            api_key=provider_config["api_key"],
            base_url=provider_config.get("base_url", "https://api.openai.com/v1"),
            model=provider_config.get("model", "gpt-4o"),
        )

    raise ValueError(f"Unknown vision provider: {provider}")
