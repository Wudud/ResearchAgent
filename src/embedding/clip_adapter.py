import logging
from pathlib import Path

from src.embedding.base_adapter import BaseEmbeddingAdapter

class CLIPEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, model_name: str = "clip-ViT-B-32", device: str = "cpu"):
        self._model_name = model_name
        self._device = device
        self._model = None
        self._logger = logging.getLogger("ResearchAgent.CLIPEmbeddingAdapter")

    @property
    def provider(self) -> str:
        return "clip"

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._model.get_sentence_embedding_dimension()

    @property
    def supports_image(self) -> bool:
        return True

    def _load_model(self):
        if self._model is not None:
            return
        self._logger.info(f"Loading CLIP model: {self._model_name}")
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name, device=self._device)
        except Exception as e:
            raise RuntimeError(f"Failed to load CLIP model {self._model_name}: {e}") from e

    def embed(self, text: str) -> list[float]:
        self._load_model()
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._load_model()
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_image(self, image_path: str) -> list[float]:
        self._load_model()
        try:
            from PIL import Image
            img = Image.open(image_path).convert("RGB")
            return self._model.encode(img, normalize_embeddings=True).tolist()
        except Exception as e:
            raise RuntimeError(f"CLIP image embedding failed for {image_path}: {e}") from e
