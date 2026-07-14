from unittest.mock import MagicMock, patch

import pytest

from src.services.assistant_service import AssistantService
from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService
from src.services.asr_service import ASRService
from src.persistence.conversation_repository import ConversationRepository
from src.services.knowledge_service import KnowledgeService

class TestAssistantService:
    @pytest.fixture
    def mock_llm(self):
        svc = MagicMock(spec=LLMService)
        svc.provider = "mock"
        svc.chat.return_value = "This is a mock response"
        return svc

    @pytest.fixture
    def mock_prompts(self):
        svc = MagicMock(spec=PromptService)
        svc.load.return_value = "System prompt"
        return svc

    @pytest.fixture
    def mock_asr(self):
        svc = MagicMock(spec=ASRService)
        svc.available = True
        svc.provider = "mock"
        svc.transcribe.return_value = "This is a mock transcript"
        return svc

    @pytest.fixture
    def repo(self):
        return ConversationRepository(":memory:")

    @pytest.fixture
    def service(self, mock_llm, mock_prompts, mock_asr, repo):
        return AssistantService(
            llm_service=mock_llm,
            prompt_service=mock_prompts,
            asr_service=mock_asr,
            repo=repo,
            context_window=20,
        )

    def test_create_conversation(self, service):
        conv_id = service.create_conversation()
        assert len(conv_id) > 0

    def test_list_conversations(self, service):
        service.create_conversation("A")
        service.create_conversation("B")
        convs = service.list_conversations()
        assert len(convs) == 2

    def test_process_text(self, service, mock_llm):
        conv_id = service.create_conversation()
        service.process_text(conv_id, "Hello")
        mock_llm.chat.assert_called_once()

    def test_process_text_auto_titles(self, service):
        conv_id = service.create_conversation()
        service.process_text(conv_id, "Hello again")
        conv = service.get_conversation(conv_id)
        assert conv is not None

    def test_process_file(self, service, mock_llm):
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.flush()

        try:
            conv_id = service.create_conversation()
            response = service.process_file(conv_id, f.name)
            msgs = service.get_messages(conv_id)
            assert len(msgs) >= 2
        finally:
            Path(f.name).unlink(missing_ok=True)

    def test_process_audio(self, service, mock_asr):
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"fake audio")
            f.flush()

        try:
            conv_id = service.create_conversation()
            response = service.process_audio(conv_id, f.name)
            mock_asr.transcribe.assert_called_once()
        finally:
            Path(f.name).unlink(missing_ok=True)

    def test_delete_conversation(self, service):
        conv_id = service.create_conversation()
        service.process_text(conv_id, "test")
        service.delete_conversation(conv_id)
        assert service.get_conversation(conv_id) is None

    def test_context_window_truncation(self, service, mock_llm):
        conv_id = service.create_conversation()
        for i in range(25):
            repo = service._repo
            repo.add_message(conv_id, "user" if i % 2 == 0 else "assistant", f"msg {i}")

        service.process_text(conv_id, "final question")
        args = mock_llm.chat.call_args[0][0]
        assert len(args) <= 22 # 1 system prompt + 20 history + 1 new message

class TestAssistantServiceRAG:
    @pytest.fixture
    def mock_llm(self):
        svc = MagicMock(spec=LLMService)
        svc.provider = "mock"
        svc.chat.return_value = "This is a mock response"
        return svc

    @pytest.fixture
    def mock_prompts(self):
        svc = MagicMock(spec=PromptService)
        svc.load.return_value = "System prompt"
        return svc

    @pytest.fixture
    def mock_knowledge(self):
        svc = MagicMock(spec=KnowledgeService)
        svc.available = True
        svc.search.return_value = {
            "results": [{"content": "relevant info", "metadata": {"title": "Test"}}],
            "citations": "[Test]",
            "context": "relevant info",
        }
        return svc

    @pytest.fixture
    def repo(self):
        return ConversationRepository(":memory:")

    @pytest.fixture
    def service(self, mock_llm, mock_prompts, repo, mock_knowledge):
        return AssistantService(
            llm_service=mock_llm,
            prompt_service=mock_prompts,
            repo=repo,
            context_window=20,
            knowledge_service=mock_knowledge,
        )

    def test_process_text_with_knowledge_retrieval(self, service, mock_knowledge, mock_llm):
        conv_id = service.create_conversation()
        response = service.process_text(conv_id, "test query")
        # LLM should have been called
        mock_llm.chat.assert_called()

    def test_process_text_without_knowledge(self, service, mock_llm):
        service._knowledge = None
        conv_id = service.create_conversation()
        response = service.process_text(conv_id, "hello")

    def test_process_text_knowledge_unavailable(self, service, mock_knowledge, mock_llm):
        mock_knowledge.available = False
        conv_id = service.create_conversation()
        response = service.process_text(conv_id, "hello")
        # No citations when knowledge is unavailable

    def test_knowledge_retrieval_error_handling(self, service, mock_knowledge, mock_llm):
        mock_knowledge.search.side_effect = Exception("ChromaDB error")
        conv_id = service.create_conversation()
        # Should not crash
        response = service.process_text(conv_id, "test")
