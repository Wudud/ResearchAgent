import logging
from pathlib import Path

from src.knowledge.indexer import Indexer

class MultimodalIndexer:
    def __init__(self, embedding_service=None, vision_service=None, persist_dir: str = "./workspace/chroma_db"):
        self._embedding = embedding_service
        self._vision = vision_service
        self._indexer = Indexer(persist_dir)
        self._logger = logging.getLogger("ResearchAgent.MultimodalIndexer")

    @property
    def available(self) -> bool:
        return self._embedding is not None and self._embedding.available

    def index_image(self, image_path: str, metadata: dict = None) -> int:
        """Index an image into the knowledge base. Returns number of chunks."""
        if not self.available:
            return 0

        path = Path(image_path)
        metadata = metadata or {}
        metadata["file"] = path.name

        # Build text representation

        if self._vision and self._vision.available:
            result = self._vision.analyze(str(path))
            if result.description:
                text_parts.append(result.description)
            if result.ocr_text:
                text_parts.append(result.ocr_text)

        text = "\n".join(text_parts)
        chunks = [{"text": text, "index": 0}]

        embedding = self._embedding.embed(text)
        self._indexer.add(
            collection_name="image",
            ids=[f"img_{path.stem}"],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
        )

        # Also index image embedding if supported
        if hasattr(self._embedding, 'supports_image') and self._embedding.supports_image:
            try:
                img_embedding = self._embedding.embed_image(str(path))
                self._indexer.add(
                    collection_name="image_vectors",
                    ids=[f"imgvec_{path.stem}"],
                    embeddings=[img_embedding],
                    documents=[text],
                    metadatas=[metadata],
                )
            except Exception as e:
                self._logger.warning(f"Image vector indexing failed: {e}")

        return 1

    def is_image(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
