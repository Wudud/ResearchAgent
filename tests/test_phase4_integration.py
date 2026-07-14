from unittest.mock import MagicMock, patch

import pytest

from src.experiment.models import Experiment
from src.meeting.models import Meeting
from src.paper.models import Paper
from src.persistence.experiment_repository import ExperimentRepository
from src.persistence.meeting_repository import MeetingRepository
from src.persistence.paper_repository import PaperRepository
from src.persistence.conversation_repository import ConversationRepository
from src.services.experiment_service import ExperimentService
from src.services.meeting_service import MeetingService
from src.services.paper_service import PaperService
from src.services.assistant_service import AssistantService
from src.services.knowledge_service import KnowledgeService
from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService

@pytest.fixture
def mock_llm():
    mock = MagicMock()
    mock.chat.return_value = '{"title": "Test", "summary": "Summary", "contributions": ["C1"], "methodology": "Method"}'
    return mock


@pytest.fixture
def mock_prompts():
    svc = MagicMock(spec=PromptService)
    svc.load.return_value = "System prompt"
    svc.render.return_value = "rendered prompt"
    return svc

@pytest.fixture
def mock_embedding():
    svc = MagicMock()
    svc.available = True
    svc.provider = "mock"
    svc.dimension = 384
    svc.embed.return_value = [0.1, 0.2, 0.3]
    svc.embed_batch.return_value = [[0.1, 0.2, 0.3]]
    return svc

@pytest.fixture
def mock_chromadb():
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_collection.query.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }
    mock_client.get_or_create_collection.return_value = mock_collection
    return mock_client


@pytest.fixture
def knowledge_service(mock_embedding, mock_chromadb):
    svc = KnowledgeService(embedding_service=mock_embedding)
    svc._indexer._client = mock_chromadb
    svc._retriever._client = mock_chromadb
    return svc


@pytest.fixture
def paper_repo():
    return PaperRepository(":memory:")


@pytest.fixture
def paper_service(mock_llm, mock_prompts, paper_repo, knowledge_service):
    return PaperService(
        llm_service=mock_llm,
        prompt_service=mock_prompts,
        paper_repo=paper_repo,
        knowledge_service=knowledge_service,
    )


def test_process_and_update_memory(paper_service):
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.flush()

        try:
            paper = paper_service.process_paper(f.name)
            assert paper.title != ""

            paper_service.update_memory(paper.id)
            # Should not raise error
        finally:
            Path(f.name).unlink(missing_ok=True)

class TestExperimentToKnowledgeIntegration:
    """Experiment → Knowledge base pipeline."""

    @pytest.fixture
    def experiment_repo(self):
        return ExperimentRepository(":memory:")

    @pytest.fixture
    def experiment_service(self, mock_llm, experiment_repo):
        return ExperimentService(llm_service=mock_llm, experiment_repo=experiment_repo)

    def test_experiment_lifecycle(self, experiment_service):
        # Create
        exp = experiment_service.create_experiment(
            name="PointNet++_Exp01",
            dataset="DairySheepHR",
            model="PointNet++",
            parameters={"lr": 0.001, "epochs": 100},
        )
        assert exp.id == 1

        # Log metrics
        experiment_service.log_metrics(exp.id, step=0, loss=1.0, mae=0.5)
        experiment_service.log_metrics(exp.id, step=1, loss=0.5, mae=0.3)

        # Start and complete
        experiment_service.start_experiment(exp.id)
        experiment_service.complete_experiment(exp.id)
        fetched = experiment_service.get_experiment(exp.id)
        assert len(fetched.metrics) >= 1

    def test_experiment_report_generation(self, experiment_service, mock_llm):
        exp = experiment_service.create_experiment(name="TestExp", dataset="DS", parameters={"lr": 0.01})
        experiment_service.log_metrics(exp.id, step=0, loss=1.0)
        report = experiment_service.generate_report(exp.id)
        assert len(report) > 0
        mock_llm.chat.assert_called_once()

    def test_experiment_comparison(self, experiment_service, mock_llm):
        e1 = experiment_service.create_experiment(name="E1", parameters={"lr": 0.001})
        e2 = experiment_service.create_experiment(name="E2", parameters={"lr": 0.01})
        experiment_service.log_metrics(e1.id, step=0, loss=1.0)
        experiment_service.log_metrics(e2.id, step=0, loss=0.5)
        comparison = experiment_service.compare_experiments([e1.id, e2.id])
        assert len(comparison) > 0

class TestFullRAGPipeline:
    """Full end-to-end: index → retrieve → assistant."""

    @pytest.fixture
    def repo(self):
        return ConversationRepository(":memory:")

    @pytest.fixture
    def assistant_service(self, mock_llm, mock_prompts, repo, knowledge_service):
        return AssistantService(
            llm_service=mock_llm,
            prompt_service=mock_prompts,
            conversation_repo=repo,
            context_window=20,
            knowledge_service=knowledge_service,
        )

    def test_rag_pipeline(self, assistant_service, knowledge_service, mock_embedding):
        knowledge_service.index_text("paper", "Test document content for RAG pipeline", {"title": "Test"})
        result = knowledge_service.search("test query")
        assert "results" in result
        assert "context" in result

        conv_id = assistant_service.create_conversation()
        response = assistant_service.process_text(conv_id, "hello")
        assert isinstance(response, str)

    def test_empty_knowledge_graceful(self, assistant_service):
        conv_id = assistant_service.create_conversation()
        response = assistant_service.process_text(conv_id, "hello")

class TestUpdateMemoryIntegration:
    """Verify update_memory works with knowledge service."""

    @pytest.fixture
    def meeting_repo(self):
        return MeetingRepository(":memory:")

    @pytest.fixture
    def paper_repo(self):
        return PaperRepository(":memory:")

    def test_meeting_update_memory_with_knowledge(self, mock_llm, mock_prompts, meeting_repo, knowledge_service, mock_embedding):
        svc = MeetingService(
            llm_service=mock_llm,
            prompt_service=mock_prompts,
            meeting_repo=meeting_repo,
            knowledge_service=knowledge_service,
        )
        meeting = svc.process_text(text="Test meeting", title="M1")
        svc.update_memory(meeting.id)
        assert mock_embedding.embed_batch.called

    def test_meeting_update_memory_without_knowledge(self, mock_llm, mock_prompts, meeting_repo):
        svc = MeetingService(
            llm_service=mock_llm,
            prompt_service=mock_prompts,
            meeting_repo=meeting_repo,
            knowledge_service=None,
        )
        meeting = svc.process_text(text="Test meeting", title="M1")
        svc.update_memory(meeting.id)

    def test_paper_update_memory_with_knowledge(self, mock_llm, mock_prompts, paper_repo, knowledge_service, mock_embedding):
        svc = PaperService(
            llm_service=mock_llm,
            prompt_service=mock_prompts,
            paper_repo=paper_repo,
            knowledge_service=knowledge_service,
        )
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.flush()

        try:
            paper = svc.process_paper(f.name)
            svc.update_memory(paper.id)
            assert mock_embedding.embed_batch.called
        finally:
            Path(f.name).unlink(missing_ok=True)

    def test_paper_update_memory_without_knowledge(self, mock_llm, mock_prompts, paper_repo):
        svc = PaperService(
            llm_service=mock_llm,
            prompt_service=mock_prompts,
            paper_repo=paper_repo,
            knowledge_service=None,
        )
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("test")
            f.flush()

        try:
            paper = svc.process_paper(f.name)
            svc.update_memory(paper.id)
            # Should not raise
        finally:
            Path(f.name).unlink(missing_ok=True)
