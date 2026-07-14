import logging
from pathlib import Path

import openai

from src.asr.base_adapter import BaseASRAdapter
from src.utils.exceptions import ASRError

class OpenAIWhisperAdapter(BaseASRAdapter):
    def __init__(self, api_key: str, model: str = "whisper-1", language: str = None):
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model
        self._language = language
        self._logger = logging.getLogger("ResearchAgent.OpenAIWhisperAdapter")

    @property
    def provider(self) -> str:
        return "openai_whisper"

    def transcribe(self, audio_path: str, language: str = None) -> str:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        lang = language or self._language

        try:
            with open(path, "rb") as f:
                kwargs = {"model": self._model, "file": f}
                if lang:
                    kwargs["language"] = lang
                transcript = self._client.audio.transcriptions.create(**kwargs)

            self._logger.info(f"Transcription complete: {len(transcript.text)} chars")
            return transcript.text
        except openai.OpenAIError as e:
            raise ASRError(f"OpenAI Whisper API error: {e}") from e
