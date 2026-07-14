import sys
from unittest.mock import MagicMock, patch

import pytest

from src.embedding.base_adapter import BaseEmbeddingAdapter
from src.embedding.local_adapter import LocalEmbeddingAdapter
from src.embedding.openai_adapter import OpenAIEmbeddingAdapter
from src.embedding.adapter_factory import create_embedding_adapter
from src.services.embedding_service import EmbeddingService
from src.config.config_manager import ConfigManager

class DummyConfig:
    def __init__(self, data: dict):
        self._data = data

    def get(self, key_path, default=None):
        keys = key_path.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

class TestLocalEmbeddingAdapter:
    @pytest.fixture
    def mock_sentence_transformers(self):
        fake_st = MagicMock()
        model = MagicMock()
        model.get_sentence_embedding_dimension.return_value = 384
        model.encode.return_value = MagicMock(tolist=MagicMock(return_value=[0.1, 0.2, 0.3]))
        fake_st.SentenceTransformer.return_value = model
        fake_st.SentenceTransformer = fake_st.SentenceTransformer
        # Lazy import does "from sentence_transformers import SentenceTransformer",
        # so we need to patch sys.modules
        with patch.dict(sys.modules, {"sentence_transformers": fake_st}):
            yield fake_st

    def test_provider(self, mock_sentence_transformers):
        adapter = LocalEmbeddingAdapter(model_name="test-model")
        assert adapter.provider == "local"

    def test_dimension(self, mock_sentence_transformers):
        adapter = LocalEmbeddingAdapter(model_name="test-model")
        assert adapter.dimension == 384

    def test_embed_single(self, mock_sentence_transformers):
        adapter = LocalEmbeddingAdapter(model_name="test-model")
        result = adapter.embed("test text")
        assert isinstance(result, list)
        assert len(result) == 3

    def test_embed_batch(self, mock_sentence_transformers):
        adapter = LocalEmbeddingAdapter(model_name="test-model")
        result = adapter.embed_batch(["text 1", "text 2"])
        assert isinstance(result, list)
        assert len(result) == 3

    def test_lazy_loading(self, mock_sentence_transformers):
        adapter = LocalEmbeddingAdapter()
        assert adapter._model is None
        adapter.embed("hello")
        assert adapter._model is not None

class TestOpenAIEmbeddingAdapter:
    @pytest.fixture
    def mock_openai(self):
        with patch("src.embedding.openai_adapter.openai") as mock:
            client = MagicMock()
            embedding_response = MagicMock()
            item = MagicMock()
            item.embedding = [0.1, 0.2, 0.3]
            item.index = 0
            embedding_response.data = [item]
            client.embeddings.create.return_value = embedding_response
            mock.OpenAI.return_value = client
            yield mock

    def test_provider(self, mock_openai):
        adapter = OpenAIEmbeddingAdapter(api_key="sk-test")
        assert adapter.provider == "openai"

    def test_embed_single(self, mock_openai):
        adapter = OpenAIEmbeddingAdapter(api_key="sk-test")
        result = adapter.embed("test")
        assert isinstance(result, list)
        assert len(result) == 3

    def test_embed_batch(self, mock_openai):
        adapter = OpenAIEmbeddingAdapter(api_key="sk-test")
        result = adapter.embed_batch(["text 1", "text 2"])
        assert isinstance(result, list)
        assert len(result) == 1  # Single response with one embedding

    def test_dimension(self, mock_openai):
        adapter = OpenAIEmbeddingAdapter(api_key="sk-test")
        d = adapter.dimension
        assert d == 3

class TestEmbeddingAdapterFactory:
    def test_create_local(self):
        config = DummyConfig({
            "embedding": {
                "default_provider": "local",
                "providers": {
                    "local": {"model_name": "test-model", "device": "cpu"},
                },
            },
        })
        with patch("src.embedding.adapter_factory.LocalEmbeddingAdapter") as mock:
            create_embedding_adapter(config)
            mock.assert_called_once_with(model_name="test-model", device="cpu")

    def test_create_openai(self):
        config = DummyConfig({
            "embedding": {
                "default_provider": "openai",
                "providers": {
                    "openai": {"api_key": "sk-test", "model": "text-embedding-3-small"},
                },
            },
        })
        # Factory instantiates OpenAI client, so mock openai at factory level
        with patch("src.embedding.adapter_factory.OpenAIEmbeddingAdapter") as mock_cls:
            create_embedding_adapter(config)
            mock_cls.assert_called_once_with(
                api_key="sk-test",
                base_url="https://api.openai.com/v1",
                model="text-embedding-3-small",
            )

    def test_create_none_when_no_provider(self):
        config = DummyConfig({"embedding": {"default_provider": None}})
        result = create_embedding_adapter(config)
        assert result is None

    def test_unknown_provider_raises(self):
        config = DummyConfig({
            "embedding": {
                "default_provider": "unknown",
                "providers": {
                    "unknown": {},
                },
            },
        })
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            create_embedding_adapter(config)

class TestEmbeddingService:
    @pytest.fixture
    def mock_adapter(self):
        adapter = MagicMock(spec=BaseEmbeddingAdapter)
        adapter.provider = "test"
        adapter.dimension = 384
        adapter.embed.return_value = [0.1, 0.2, 0.3]
        adapter.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        return adapter

    def test_embed(self, mock_adapter):
        svc = EmbeddingService(mock_adapter)
        result = svc.embed("test")
        assert result == [0.1, 0.2, 0.3]
        mock_adapter.embed.assert_called_once_with("test")

    def test_embed_batch(self, mock_adapter):
        svc = EmbeddingService(mock_adapter)
        result = svc.embed_batch(["a", "b"])
        assert len(result) == 2
        mock_adapter.embed_batch.assert_called_once_with(["a", "b"])

    def test_available(self, mock_adapter):
        svc = EmbeddingService(mock_adapter)
        assert svc.available is True
        assert svc.provider == "test"
        assert svc.dimension == 384

    def test_unavailable(self):
        svc = EmbeddingService(None)
        assert svc.available is False
        assert svc.provider == "none"
        assert svc.dimension == 0

    def test_embed_without_adapter_raises(self):
        svc = EmbeddingService(None)
        with pytest.raises(RuntimeError, match="Embedding"):
            svc.embed("test")

    def test_embed_batch_without_adapter_raises(self):
        svc = EmbeddingService(None)
        with pytest.raises(RuntimeError, match="Embedding"):
            svc.embed_batch(["test"])
