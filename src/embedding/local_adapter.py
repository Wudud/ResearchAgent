import logging

from src.embedding.base_adapter import BaseEmbeddingAdapter

class LocalEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        self._model_name = model_name
        self._device = device
        self._model = None
        self._logger = logging.getLogger("ResearchAgent.LocalEmbeddingAdapter")

    @property
    def provider(self) -> str:
        return "local"

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._model.get_sentence_embedding_dimension()

    def _load_model(self):
        if self._model is not None:
            return
        self._logger.info(f"Loading embedding model: {self._model_name}")
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name, device=self._device)
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model {self._model_name}: {e}") from e

    def embed(self, text: str) -> list[float]:
        self._load_model()
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._load_model()
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
