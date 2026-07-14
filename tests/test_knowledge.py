from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.knowledge.chunker import Chunker
from src.knowledge.citation import Citation

class TestChunker:
    @pytest.fixture
    def chunker(self):
        return Chunker(chunk_size=256, chunk_overlap=50)

    def test_empty_text(self, chunker):
        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []

    def test_short_text(self, chunker):
        text = "Hello world. This is a short text."
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["index"] == 0

    def test_long_text(self, chunker):
        text = "A" * 1000
        chunks = chunker.chunk(text)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c["text"]) <= 300

    def test_chunk_indices(self, chunker):
        text = "B" * 800
        chunks = chunker.chunk(text)
        indices = [c["index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_english_text(self, chunker):
        text = "This is a test sentence. It should be split properly. " * 20
        chunks = chunker.chunk(text)
        assert len(chunks) > 1

    def test_normalize_whitespace(self, chunker):
        text = "Line 1\n\n\n\nLine 2  with   spaces"
        chunks = chunker.chunk(text)
        assert "\n\n\n" not in chunks[0]["text"]
        assert "  " not in chunks[0]["text"]

    def test_custom_chunk_size(self):
        chunker = Chunker(chunk_size=100, chunk_overlap=10)
        text = "A" * 500
        chunks = chunker.chunk(text)
        for c in chunks:
            assert len(c["text"]) <= 110  # 100 + small margin

class TestCitation:
    @pytest.fixture
    def citation(self):
        return Citation()

    @pytest.fixture
    def sample_result(self):
        return {
            "id": "test_1",
            "document": "A test document",
            "metadata": {
                "title": "Test Paper",
                "source_type": "paper",
                "authors": "Author1, Author2",
            },
            "distance": 0.15,
            "collection": "paper",
        }

    def test_format_single(self, citation, sample_result):
        formatted = citation.format(sample_result)
        assert "Test Paper" in formatted

    def test_format_batch(self, citation):
        results = [
            {
                "metadata": {"title": "Paper A", "source_type": "paper"},
                "collection": "paper",
                "id": "1", "document": "...", "distance": 0.1,
            },
            {
                "metadata": {"title": "Meeting B", "source_type": "meeting"},
                "collection": "meeting",
                "id": "2", "document": "...", "distance": 0.2,
            },
        ]
        formatted = citation.format_batch(results)
        assert "Paper A" in formatted
        assert "Meeting B" in formatted

    def test_format_batch_empty(self, citation):
        assert citation.format_batch([]) == ""

    def test_inline_citations(self, citation):
        results = [
            {"metadata": {"title": "Paper X", "source_type": "paper"}},
        ]
        inline = citation.inline_citations(results)
        assert "Paper X" in inline

    def test_source_label_unknown(self, citation):
        result = {
            "metadata": {"title": "Something", "source_type": "unknown_type"},
            "collection": "unknown_type",
            "id": "1", "document": "...", "distance": 0.1,
        }
        formatted = citation.format(result)
        assert "unknown_type" in formatted

class TestRetriever:
    @pytest.fixture
    def mock_chromadb(self):
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 3
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"title": "T1", "source_type": "paper"}, {"title": "T2", "source_type": "meeting"}]],
            "distances": [[0.1, 0.2]],
        }
        mock_client.get_collection.return_value = mock_collection
        mock_client.list_collections.return_value = ["paper", "meeting"]

        with patch("src.knowledge.retriever.chromadb.PersistentClient", return_value=mock_client):
            yield mock_client

    def test_retrieve(self, mock_chromadb):
        from src.knowledge.retriever import Retriever
        retriever = Retriever()
        results = retriever.retrieve([0.1, 0.2, 0.3], top_k=2)
        # Results are capped at top_k after sorting across collections
        assert len(results) == 2
        assert results[0]["metadata"]["title"] == "T1"

    def test_retrieve_specific_collections(self, mock_chromadb):
        from src.knowledge.retriever import Retriever
        retriever = Retriever()
        results = retriever.retrieve([0.1, 0.2], collection_names=["paper"], top_k=2)
        assert len(results) == 2

class TestIndexer:
    @pytest.fixture
    def mock_chromadb(self):
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client.get_collection.return_value = mock_collection
        mock_client.list_collections.return_value = ["paper"]

        with patch("src.knowledge.indexer.chromadb.PersistentClient", return_value=mock_client):
            yield mock_client

    def test_add(self, mock_chromadb):
        from src.knowledge.indexer import Indexer
        indexer = Indexer()
        indexer.add(
            collection_name="paper",
            ids=["p1", "p2"],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            documents=["doc1", "doc2"],
            metadatas=[{"title": "T1"}, {"title": "T2"}],
        )
        assert mock_chromadb.get_or_create_collection.called

    def test_collection_count(self, mock_chromadb):
        from src.knowledge.indexer import Indexer
        indexer = Indexer()
        assert indexer.collection_count("paper") == 5

    def test_delete_collection(self, mock_chromadb):
        from src.knowledge.indexer import Indexer
        indexer = Indexer()
        indexer.delete_collection("paper")
        assert mock_chromadb.delete_collection.called

class TestKnowledgeService:
    @pytest.fixture
    def mock_embedding(self):
        svc = MagicMock()
        svc.available = True
        svc.provider = "mock"
        svc.dimension = 384
        svc.embed.return_value = [0.1, 0.2, 0.3]
        svc.embed_batch.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        return svc

    @pytest.fixture
    def mock_chromadb(self):
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 2
        mock_collection.query.return_value = {
            "ids": [["id1"]],
            "documents": [["test document"]],
            "metadatas": [[{"title": "Test", "source_type": "paper"}]],
            "distances": [[0.1]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client.get_collection.return_value = mock_collection
        mock_client.list_collections.return_value = ["paper"]

        with patch("src.knowledge.indexer.chromadb.PersistentClient", return_value=mock_client), \
             patch("src.knowledge.retriever.chromadb.PersistentClient", return_value=mock_client):
            yield mock_client

    def test_index_text(self, mock_embedding, mock_chromadb):
        from src.services.knowledge_service import KnowledgeService
        svc = KnowledgeService(embedding_service=mock_embedding)
        count = svc.index_text("paper", "This is a test document. " * 20, {"title": "Test"})
        assert count > 0

    def test_index_text_no_embedding(self, mock_chromadb):
        from src.services.knowledge_service import KnowledgeService
        svc = KnowledgeService(embedding_service=None)
        count = svc.index_text("paper", "test", {})
        assert count == 0

    def test_retrieve(self, mock_embedding, mock_chromadb):
        from src.services.knowledge_service import KnowledgeService
        svc = KnowledgeService(embedding_service=mock_embedding)
        results = svc.retrieve("test query", top_k=3)
        assert len(results) >= 1
        mock_embedding.embed.assert_called_once_with("test query")

    def test_search(self, mock_embedding, mock_chromadb):
        from src.services.knowledge_service import KnowledgeService
        svc = KnowledgeService(embedding_service=mock_embedding)
        result = svc.search("test query")
        assert "results" in result
        assert "citations" in result
        assert "context" in result

    def test_available(self, mock_embedding, mock_chromadb):
        from src.services.knowledge_service import KnowledgeService
        svc = KnowledgeService(embedding_service=mock_embedding)
        assert svc.available is True

    def test_not_available_without_embedding(self, mock_chromadb):
        from src.services.knowledge_service import KnowledgeService
        svc = KnowledgeService(embedding_service=None)
        assert svc.available is False

    def test_clear_source(self, mock_embedding, mock_chromadb):
        from src.services.knowledge_service import KnowledgeService
        svc = KnowledgeService(embedding_service=mock_embedding)
        svc.clear_source("paper")
        assert mock_chromadb.delete_collection.called

    def test_get_source_count(self, mock_embedding, mock_chromadb):
        from src.services.knowledge_service import KnowledgeService
        svc = KnowledgeService(embedding_service=mock_embedding)
        assert svc.get_source_count("paper") == 2
