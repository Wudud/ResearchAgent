import logging

from src.asr.base_adapter import BaseASRAdapter

class ASRService:
    def __init__(self, adapter: BaseASRAdapter = None):
        self._adapter = adapter
        self._logger = logging.getLogger("ResearchAgent.ASRService")

    @property
    def provider(self) -> str:
        return self._adapter.provider if self._adapter else "none"

    @property
    def available(self) -> bool:
        return self._adapter is not None

    def transcribe(self, audio_path: str, language: str = None) -> str:
        if self._adapter is None:
            raise RuntimeError("ASR service is not configured.")

        self._logger.info(f"Transcribing: {audio_path} (provider={self.provider})")
        return self._adapter.transcribe(audio_path, language=language)
