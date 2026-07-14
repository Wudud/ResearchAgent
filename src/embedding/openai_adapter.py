import logging

import openai

from src.embedding.base_adapter import BaseEmbeddingAdapter


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1",
                 model: str = "text-embedding-3-small"):
        self._api_key = api_key
        self._base_url = base_url
        self._model_name = model
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._logger = logging.getLogger("ResearchAgent.OpenAIEmbeddingAdapter")
        self._dim = None

    @property
    def provider(self) -> str:
        return "openai"

    @property
    def dimension(self) -> int:
        if self._dim is None:
            # Detect dimension from a small test call
            test = self.embed("dimension test")
            self._dim = len(test)
        return self._dim

    def embed(self, text: str) -> list[float]:
        try:
            response = self._client.embeddings.create(
                model=self._model_name,
                input=text,
            )
            return response.data[0].embedding
        except openai.OpenAIError as e:
            raise RuntimeError(f"OpenAI Embedding error: {e}") from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._client.embeddings.create(
                model=self._model_name,
                input=texts,
            )
            # Sort by index to maintain order
            results = sorted(response.data, key=lambda x: x.index)
            return [r.embedding for r in results]
        except openai.OpenAIError as e:
            raise RuntimeError(f"OpenAI Embedding error: {e}") from e
