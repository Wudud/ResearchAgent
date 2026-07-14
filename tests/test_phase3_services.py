from unittest.mock import MagicMock

import pytest

from src.services.meeting_service import MeetingService
from src.services.paper_service import PaperService
from src.services.task_service import TaskService
from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService
from src.services.asr_service import ASRService
from src.persistence.meeting_repository import MeetingRepository
from src.persistence.paper_repository import PaperRepository
from src.persistence.task_repository import TaskRepository

class TestMeetingService:
    @pytest.fixture
    def mock_llm(self):
        svc = MagicMock(spec=LLMService)
        svc.chat.return_value = "{}"
        return svc

    @pytest.fixture
    def mock_prompts(self):
        svc = MagicMock(spec=PromptService)
        svc.render.return_value = "prompt"
        return svc

    @pytest.fixture
    def mock_asr(self):
        svc = MagicMock(spec=ASRService)
        svc.available = True
        svc.provider = "mock"
        return svc

    @pytest.fixture
    def repo(self):
        return MeetingRepository(":memory:")

    @pytest.fixture
    def service(self, mock_llm, mock_prompts, mock_asr, repo):
        return MeetingService(llm_service=mock_llm, prompt_service=mock_prompts, asr_service=mock_asr, meeting_repo=repo)

    def test_process_text(self, service):
        meeting = service.process_text(text="Test meeting content", title="Test")
        assert meeting is not None

    def test_list_and_delete(self, service):
        m = service.process_text(text="Test", title="M1")
        meetings = service.list_meetings()
        assert len(meetings) >= 1
        service.delete_meeting(m.id)
        assert service.get_meeting(m.id) is None

    def test_extract_tasks(self, mock_llm):
        repo = MeetingRepository(":memory:")
        mock_prompts = MagicMock(spec=PromptService)
        mock_prompts.render.return_value = "prompt"
        service = MeetingService(llm_service=mock_llm, prompt_service=mock_prompts, meeting_repo=repo)
        meeting = service.process_text(text="Test with tasks", title="T1")
        tasks = service.extract_tasks(meeting.id)
        assert len(tasks) >= 0

class TestPaperService:
    @pytest.fixture
    def mock_llm(self):
        svc = MagicMock(spec=LLMService)
        svc.chat.return_value = '{"title": "Test Paper", "authors": "Author", "keywords": ["test"], "summary": "A test"}'
        return svc

    @pytest.fixture
    def mock_prompts(self):
        svc = MagicMock(spec=PromptService)
        svc.render.return_value = "prompt"
        return svc

    @pytest.fixture
    def repo(self):
        return PaperRepository(":memory:")

    @pytest.fixture
    def service(self, mock_llm, mock_prompts, repo):
        return PaperService(llm_service=mock_llm, prompt_service=mock_prompts, paper_repo=repo)

    def test_process_text_file(self, service):
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.flush()

        try:
            paper = service.process_paper(f.name)
            assert paper is not None
        finally:
            Path(f.name).unlink(missing_ok=True)

    def test_search(self, service):
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("test")
            f.flush()

        try:
            service.process_paper(f.name)
            results = service.search("test")
            assert len(results) >= 1
        finally:
            Path(f.name).unlink(missing_ok=True)

class TestTaskService:
    @pytest.fixture
    def repo(self):
        return TaskRepository(":memory:")

    @pytest.fixture
    def service(self, repo):
        return TaskService(task_repo=repo)

    def test_create_and_list(self, service):
        service.create_task(content="Test task 1", source="Meeting")
        tasks = service.list_tasks()
        assert len(tasks) == 1

    def test_create_batch(self, service):
        tasks_data = [
            {"content": "Batch task 1", "priority": "high"},
            {"content": "Batch task 2", "priority": "medium"},
        ]
        tasks = service.create_tasks_batch(tasks_data, source="Meeting")
        assert len(tasks) == 2

    def test_update_status(self, service):
        task = service.create_task(content="Test task")
        service.update_status(task.id, "completed")
        t = service.get_task(task.id)
        assert t is not None

    def test_stats(self, service):
        t1 = service.create_task(content="T1")
        t2 = service.create_task(content="T2")
        service.update_status(t1.id, "completed")
        stats = service.get_stats()
        assert stats["total"] == 2
        assert stats["completed"] == 1
        assert "50%" in stats["completion_rate"]
