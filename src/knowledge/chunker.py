import re

class Chunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[dict]:
        """Split text into chunks with metadata. Returns list of {text, index}."""
        if not text or not text.strip():
            return []

        # Normalize whitespace while preserving paragraphs
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        chunks = []
        start = 0
        idx = 0

        while start < len(text):
            end = start + self.chunk_size

            if end >= len(text):
                chunk_text = text[start:].strip()
            else:
                # Try to break at sentence boundary
                chunk_text = text[start:end]
                # Look for the last sentence-ending marker
                cut = max(
                    chunk_text.rfind("。"),
                    chunk_text.rfind(". "),
                    chunk_text.rfind("！"),
                    chunk_text.rfind("？"),
                    chunk_text.rfind("\n"),
                    chunk_text.rfind("? "),
                    chunk_text.rfind("! "),
                )
                if cut > self.chunk_size // 2:
                    end = start + cut + 1
                    chunk_text = text[start:end].strip()
                else:
                    chunk_text = chunk_text.strip()

            if chunk_text:
                chunks.append({"text": chunk_text, "index": idx})
                idx += 1

            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks
