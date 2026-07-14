from unittest.mock import MagicMock, patch

import pytest

from src.asr.local_whisper_adapter import LocalWhisperAdapter
from src.asr.openai_whisper_adapter import OpenAIWhisperAdapter
from src.asr.adapter_factory import create_asr_adapter
from src.utils.exceptions import ASRError

class TestLocalWhisperAdapter:
    def test_provider(self):
        adapter = LocalWhisperAdapter()
        assert adapter.provider == "local_whisper"

    def test_transcribe_file_not_found(self):
        adapter = LocalWhisperAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.transcribe("/nonexistent/audio.wav")

    def test_transcribe_success(self):
        mock_model = MagicMock()
        mock_segment = MagicMock()
        mock_segment.text = "test transcription"
        mock_info = MagicMock()
        mock_info.language = "zh"
        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"fake audio data")
            f.flush()

        try:
            adapter = LocalWhisperAdapter()
            adapter._model = mock_model
            result = adapter.transcribe(f.name)
        finally:
            Path(f.name).unlink(missing_ok=True)

class TestOpenAIWhisperAdapter:
    def test_provider(self):
        adapter = OpenAIWhisperAdapter(api_key="sk-test")
        assert adapter.provider == "openai_whisper"

    @patch("src.asr.openai_whisper_adapter.openai.OpenAI")
    def test_transcribe_success(self, mock_openai_class):
        mock_client = MagicMock()
        mock_transcript = MagicMock()
        mock_transcript.text = "Transcription result"
        mock_client.audio.transcriptions.create.return_value = mock_transcript
        mock_openai_class.return_value = mock_client

        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"fake audio")
            f.flush()

        try:
            adapter = OpenAIWhisperAdapter(api_key="sk-test")
            adapter._client = mock_client
            result = adapter.transcribe(f.name)
            assert result == "Transcription result"
        finally:
            Path(f.name).unlink(missing_ok=True)

class TestASRFactory:
    def test_create_none_when_provider_is_none(self):
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: None
        adapter = create_asr_adapter(mock_config)
        assert adapter is None

    def test_create_local_adapter(self):
        mock_config = MagicMock()
        def getter(key, default=None):
            if key == "asr.default_provider":
                return "local"
            if key == "asr.providers.local":
                return {"model_size": "tiny", "device": "cpu", "compute_type": "int8"}
            return default
        mock_config.get = getter
        adapter = create_asr_adapter(mock_config)
        assert isinstance(adapter, LocalWhisperAdapter)
