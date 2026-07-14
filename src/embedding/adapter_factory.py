from src.embedding.base_adapter import BaseEmbeddingAdapter
from src.embedding.local_adapter import LocalEmbeddingAdapter
from src.embedding.openai_adapter import OpenAIEmbeddingAdapter
from src.embedding.clip_adapter import CLIPEmbeddingAdapter


def create_embedding_adapter(config) -> BaseEmbeddingAdapter | None:
    provider = config.get("embedding.default_provider")
    if provider is None:
        return None

    provider_config = config.get(f"embedding.providers.{provider}")
    if provider_config is None:
        raise ValueError(f"Embedding provider '{provider}' not found in config")

    if provider == "local":
        return LocalEmbeddingAdapter(
            model_name=provider_config.get("model_name", "all-MiniLM-L6-v2"),
            device=provider_config.get("device", "cpu"),
        )

    if provider == "openai":
        return OpenAIEmbeddingAdapter(
            api_key=provider_config["api_key"],
            base_url=provider_config.get("base_url", "https://api.openai.com/v1"),
            model=provider_config.get("model", "text-embedding-3-small"),
        )

    if provider == "clip":
        return CLIPEmbeddingAdapter(
            model_name=provider_config.get("model_name", "clip-ViT-B-32"),
            device=provider_config.get("device", "cpu"),
        )

    raise ValueError(f"Unknown embedding provider: {provider}")
