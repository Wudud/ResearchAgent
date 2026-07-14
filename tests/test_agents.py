"""
Agent测试模块 - 测试BaseAgent、各领域Agent和AgentCoordinator。

验证ReAct循环、工具注册和任务分发功能。
"""

from unittest.mock import MagicMock

import pytest

from src.agents.base import BaseAgent
from src.agents.paper import PaperAgent
from src.agents.meeting import MeetingAgent
from src.agents.experiment import ExperimentAgent
from src.agents.dataset import DatasetAgent
from src.agents.coordinator import AgentCoordinator
from src.reasoning.reasoning_service import ReasoningService


@pytest.fixture
def mock_llm():
    """创建模拟的LLM服务。"""
    mock = MagicMock()
    mock.chat.return_value = '{"type": "finish", "summary": "Done"}'
    return mock


@pytest.fixture
def reasoning(mock_llm):
    """创建推理服务实例。"""
    return ReasoningService(llm_service=mock_llm, max_iterations=3)


@pytest.fixture
def mock_manager():
    """创建模拟的管理器。"""
    mgr = MagicMock()
    mgr.list_papers.return_value = []
    mgr.process_paper.return_value = MagicMock(title="Test")
    mgr.search_paper.return_value = []
    mgr.get_paper.return_value = None
    mgr.delete_paper.return_value = None
    return mgr


class TestBaseAgent:
    """测试BaseAgent的ReAct循环功能。"""

    def test_run_completes(self, reasoning, mock_manager):
        """测试basic run completes successfully。"""
        class TestAgent(BaseAgent):
            def _register_tools(self):
                self._add_tool("test", "test tool", lambda: "done")

        agent = TestAgent("test", mock_manager, reasoning, "You are a tester.")
        result = agent.run("say hello")
        assert result["status"] == "completed"
        assert "summary" in result

    def test_run_with_action(self, reasoning, mock_llm, mock_manager):
        """测试带工具调用的ReAct循环。"""
        mock_llm.chat.side_effect = [
            '{"type": "action", "tool": "test", "args": {}}',
            '{"type": "finish", "summary": "Complete!"}',
        ]

        class TestAgent(BaseAgent):
            def _register_tools(self):
                self._add_tool("test", "test tool", lambda: "ok")

        agent = TestAgent("test", mock_manager, reasoning)
        result = agent.run("do something")
        assert result["status"] == "completed"
        assert len(result["steps"]) == 2
        assert result["steps"][0]["type"] == "action"
        assert result["steps"][1]["type"] == "finish"


class TestDomainAgents:
    """测试各领域Agent的工具注册。"""

    def test_paper_agent_tools_registered(self, reasoning, mock_manager):
        """测试PaperAgent工具注册。"""
        agent = PaperAgent(mock_manager, reasoning)
        assert len(agent._tools) >= 4

    def test_meeting_agent_tools_registered(self, reasoning, mock_manager):
        """测试MeetingAgent工具注册。"""
        agent = MeetingAgent(mock_manager, reasoning)
        assert len(agent._tools) >= 4

    def test_experiment_agent_tools_registered(self, reasoning, mock_manager):
        """测试ExperimentAgent工具注册。"""
        agent = ExperimentAgent(mock_manager, reasoning)
        assert len(agent._tools) >= 6

    def test_dataset_agent_tools_registered(self, reasoning, mock_manager):
        """测试DatasetAgent工具注册。"""
        agent = DatasetAgent(mock_manager, reasoning)
        assert len(agent._tools) >= 4
