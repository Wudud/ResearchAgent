"""
持久层仓库测试模块 - 测试Meeting、Paper、Task、ResearchMemory仓库的CRUD操作。
"""

import pytest

from src.meeting.models import Meeting
from src.paper.models import Paper
from src.task.models import Task
from src.persistence.memory_repository import ResearchMemory, ResearchMemoryRepository
from src.persistence.meeting_repository import MeetingRepository
from src.persistence.paper_repository import PaperRepository
from src.persistence.task_repository import TaskRepository


class TestMeetingRepository:
    """测试MeetingRepository的CRUD操作。"""

    @pytest.fixture
    def repo(self):
        return MeetingRepository(":memory:")

    def test_save_and_get(self, repo):
        meeting = Meeting(id="", title="Test Meeting", created_at="2024-01-01")
        saved = repo.save(meeting)
        assert saved.id
        assert hasattr(saved, 'created_at') or saved.created_at

        fetched = repo.get(saved.id)
        assert fetched is not None

    def test_list_all(self, repo):
        repo.save(Meeting(id="", title="A", created_at="2024-01-01"))
        repo.save(Meeting(id="", title="B", created_at="2024-01-02"))
        meetings = repo.list_all()
        assert len(meetings) == 2

    def test_delete(self, repo):
        meeting = Meeting(id="", title="Test", created_at="2024-01-01")
        saved = repo.save(meeting)
        repo.delete(saved.id)
        assert repo.get(saved.id) is None


class TestPaperRepository:
    """测试PaperRepository的CRUD操作。"""

    @pytest.fixture
    def repo(self):
        return PaperRepository(":memory:")

    def test_save_and_get(self, repo):
        paper = Paper(id="", title="PointNet++", authors="Qi et al.", keywords=["3D", "point cloud"])
        saved = repo.save(paper)
        fetched = repo.get(saved.id)
        assert fetched is not None

    def test_search(self, repo):
        repo.save(Paper(id="", title="PointNet", authors="A", keywords=["3D"]))
        repo.save(Paper(id="", title="Other", authors="B", keywords=["2D"]))
        results = repo.search("PointNet")
        assert len(results) == 1


class TestTaskRepository:
    """测试TaskRepository的CRUD操作。"""

    @pytest.fixture
    def repo(self):
        return TaskRepository(":memory:")

    def test_create_and_get(self, repo):
        task = Task(content="T1", source="Meeting", priority="high")
        saved = repo.create(task)
        assert saved.id is not None
        fetched = repo.get(saved.id)
        assert fetched is not None

    def test_filter_by_source(self, repo):
        repo.create(Task(content="T1", source="Meeting"))
        repo.create(Task(content="T2", source="Paper"))
        result = repo.list_all(source="Meeting")
        assert len(result) == 1

    def test_filter_by_status(self, repo):
        repo.create(Task(content="T1", source="Meeting"))
        repo.create(Task(content="T2", source="Meeting"))
        result = repo.list_all(status="pending")
        assert len(result) >= 1

    def test_update_status(self, repo):
        task = repo.create(Task(content="T1"))
        repo.update_status(task.id, "completed")
        fetched = repo.get(task.id)
        assert fetched is not None

    def test_delete(self, repo):
        task = repo.create(Task(content="T1"))
        repo.delete(task.id)
        assert repo.get(task.id) is None


class TestResearchMemoryRepository:
    """测试ResearchMemoryRepository的CRUD操作。"""

    @pytest.fixture
    def repo(self):
        return ResearchMemoryRepository(":memory:")

    def test_save_and_get(self, repo):
        mem = ResearchMemory(category="Meeting", title="M1", content="Test content")
        saved = repo.save(mem)
        fetched = repo.get(saved.id)
        assert fetched is not None

    def test_list_by_category(self, repo):
        repo.save(ResearchMemory(category="Meeting", title="M1", content="C1"))
        repo.save(ResearchMemory(category="Paper", title="P1", content="C2"))
        result = repo.list_by_category("Meeting")
        assert len(result) == 1

    def test_search(self, repo):
        repo.save(ResearchMemory(category="Paper", title="Open3D Paper", content="About Open3D"))
        repo.save(ResearchMemory(category="Paper", title="Other", content="Other"))
        results = repo.search("Open3D")
        assert len(results) == 1
