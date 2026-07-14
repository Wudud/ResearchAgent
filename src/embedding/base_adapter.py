from abc import ABC, abstractmethod


class BaseEmbeddingAdapter(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Encode a single text into a vector."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts into vectors."""
        ...

    def embed_image(self, image_path: str) -> list[float] | None:
        """Optional: encode an image into a vector. Returns None if not supported."""
        return None

    @property
    @abstractmethod
    def provider(self) -> str:
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...

    @property
    def supports_image(self) -> bool:
        return False
