from unittest.mock import MagicMock, patch

import pytest

from src.llm.openai_adapter import OpenAIAdapter
from src.utils.exceptions import LLMError

class TestOpenAIAdapter:
    @pytest.fixture
    def adapter(self):
        return OpenAIAdapter(
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            model="gpt-4o",
        )

    def test_provider(self, adapter):
        assert adapter.provider == "openai"

    @patch("src.llm.openai_adapter.openai.OpenAI")
    def test_chat_returns_content(self, mock_openai_class, adapter):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from GPT"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        adapter._client = mock_client
        result = adapter.chat([{"role": "user", "content": "Hi"}])

        assert result == "Hello from GPT"
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.llm.openai_adapter.openai.OpenAI")
    def test_chat_raises_llm_error(self, mock_openai_class, adapter):
        import openai

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.OpenAIError("API down")
        mock_openai_class.return_value = mock_client

        adapter._client = mock_client
        with pytest.raises(LLMError, match="API down"):
            adapter.chat([{"role": "user", "content": "Hi"}])

    @patch("src.llm.openai_adapter.openai.OpenAI")
    def test_chat_stream_yields_chunks(self, mock_openai_class, adapter):
        mock_client = MagicMock()
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello"
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " World"
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = None
        mock_client.chat.completions.create.return_value = [chunk1, chunk2, chunk3]
        mock_openai_class.return_value = mock_client

        adapter._client = mock_client
        result = list(adapter.chat_stream([{"role": "user", "content": "Hi"}]))

        assert result == ["Hello", " World"]
