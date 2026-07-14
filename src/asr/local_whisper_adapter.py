import logging
from pathlib import Path

from src.asr.base_adapter import BaseASRAdapter
from src.utils.exceptions import ASRError

class LocalWhisperAdapter(BaseASRAdapter):
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None
        self._logger = logging.getLogger("ResearchAgent.LocalWhisperAdapter")

    @property
    def provider(self) -> str:
        return "local_whisper"

    def _load_model(self):
        if self._model is not None:
            return

        self._logger.info(f"Loading Whisper model: {self._model_size} on {self._device}")
        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
        except Exception as e:
            raise ASRError(f"Failed to load local Whisper model: {e}") from e

    def transcribe(self, audio_path: str, language: str = None) -> str:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()

        try:
            segments, info = self._model.transcribe(str(path), language=language, beam_size=5)
            text = " ".join(seg.text.strip() for seg in segments)
            self._logger.info(f"Transcription complete: {len(text)} chars, language={info.language}")
            return text
        except Exception as e:
            raise ASRError(f"Transcription failed: {e}") from e
