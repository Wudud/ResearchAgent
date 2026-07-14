from src.asr.base_adapter import BaseASRAdapter
from src.asr.local_whisper_adapter import LocalWhisperAdapter
from src.asr.openai_whisper_adapter import OpenAIWhisperAdapter


def create_asr_adapter(config) -> BaseASRAdapter | None:
    provider = config.get("asr.default_provider")
    if provider is None:
        return None

    provider_config = config.get(f"asr.providers.{provider}")
    if provider_config is None:
        raise ValueError(f"ASR provider '{provider}' not found in config")

    if provider == "local":
        return LocalWhisperAdapter(
            model_size=provider_config.get("model_size", "base"),
            device=provider_config.get("device", "cpu"),
            compute_type=provider_config.get("compute_type", "int8"),
        )

    if provider == "openai":
        return OpenAIWhisperAdapter(
            api_key=provider_config["api_key"],
            model=provider_config.get("model", "whisper-1"),
            language=provider_config.get("language"),
        )

    raise ValueError(f"Unknown ASR provider: {provider}")
