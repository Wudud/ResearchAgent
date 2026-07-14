from unittest.mock import MagicMock, patch

import pytest

from src.workflows.base_workflow import BaseWorkflow
from src.workflows.research_workflow import PaperWorkflow, MeetingWorkflow, ExperimentWorkflow, DatasetWorkflow
from src.workflows.auto_index_workflow import AutoIndexWorkflow

@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.managers = {}
    agent.services = {}
    return agent


@pytest.fixture
def mock_paper():
    paper = MagicMock()
    paper.id = "p1"
    paper.title = "Test Paper"
    return paper


@pytest.fixture
def mock_meeting():
    meeting = MagicMock()
    meeting.id = "m1"
    meeting.title = "Test Meeting"
    return meeting


@pytest.fixture
def mock_experiment():
    exp = MagicMock()
    exp.id = 1
    exp.name = "TestExp"
    return exp

class TestBaseWorkflow:
    def test_run_raises_not_implemented(self, mock_agent):
        wf = BaseWorkflow("test", agent=mock_agent)
        with pytest.raises(NotImplementedError):
            wf.run()

class TestPaperWorkflow:
    def test_run(self, mock_agent, mock_paper):
        paper_mgr = MagicMock()
        paper_mgr.process_paper.return_value = mock_paper
        knowledge_mgr = MagicMock()
        task_mgr = MagicMock()
        mock_agent.managers = {"paper": paper_mgr, "knowledge": knowledge_mgr, "task": task_mgr}

        wf = PaperWorkflow("test", agent=mock_agent)
        result = wf.run(file_path="/test.pdf")

        assert result["status"] == "completed"
        paper_mgr.process_paper.assert_called_once_with("/test.pdf")
        knowledge_mgr.index_paper.assert_called_once()
        assert task_mgr.create_task.call_count > 0

    def test_run_without_auto_index(self, mock_agent, mock_paper):
        paper_mgr = MagicMock()
        paper_mgr.process_paper.return_value = mock_paper
        knowledge_mgr = MagicMock()
        mock_agent.managers = {"paper": paper_mgr, "knowledge": knowledge_mgr}

        wf = PaperWorkflow("test", agent=mock_agent)
        result = wf.run(file_path="/test.pdf", auto_index=False)

        assert result["status"] == "completed"
        knowledge_mgr.index_paper.assert_not_called()

    def test_run_missing_manager(self, mock_agent):
        mock_agent.managers = {}
        wf = PaperWorkflow("test", agent=mock_agent)
        result = wf.run(file_path="/test.pdf")
        assert result["status"] == "error"

class TestMeetingWorkflow:
    def test_run_with_text(self, mock_agent, mock_meeting):
        meeting_mgr = MagicMock()
        meeting_mgr.process_meeting_text.return_value = mock_meeting
        knowledge_mgr = MagicMock()
        task_mgr = MagicMock()
        mock_agent.managers = {"meeting": meeting_mgr, "knowledge": knowledge_mgr, "task": task_mgr}

        wf = MeetingWorkflow("test", agent=mock_agent)
        result = wf.run(text="This is a test meeting transcript")

        assert result["status"] == "completed"

    def test_run_missing_input(self, mock_agent):
        meeting_mgr = MagicMock()
        mock_agent.managers = {"meeting": meeting_mgr}
        wf = MeetingWorkflow("test", agent=mock_agent)
        result = wf.run()
        assert result["status"] == "error"

class TestExperimentWorkflow:
    def test_run(self, mock_agent, mock_experiment):
        exp_mgr = MagicMock()
        exp_mgr.create_experiment.return_value = mock_experiment
        exp_mgr.generate_report.return_value = "# Report"
        knowledge_mgr = MagicMock()
        mock_agent.managers = {"experiment": exp_mgr, "knowledge": knowledge_mgr}

        wf = ExperimentWorkflow("test", agent=mock_agent)
        result = wf.run(name="Exp01", dataset="DS", parameters={"lr": 0.01},
                        metrics=[{"step": 0, "loss": 1.0}])

        assert result["status"] == "completed"
        exp_mgr.create_experiment.assert_called_once()
        exp_mgr.log_metrics.assert_called_once()
        knowledge_mgr.index_experiment.assert_called_once()

class TestAutoIndexWorkflow:
    def test_run(self, mock_agent):
        paper_mgr = MagicMock()
        paper_mgr.list_papers.return_value = [MagicMock()]
        meeting_mgr = MagicMock()
        meeting_mgr.list_meetings.return_value = [MagicMock()]
        exp_mgr = MagicMock()
        exp_mgr.list_experiments.return_value = []
        knowledge_mgr = MagicMock()
        knowledge_mgr.index_paper.return_value = 2
        knowledge_mgr.index_meeting.return_value = 3

        mock_agent.managers = {
            "paper": paper_mgr, "meeting": meeting_mgr,
            "experiment": exp_mgr, "knowledge": knowledge_mgr,
        }

        wf = AutoIndexWorkflow("test", agent=mock_agent)
        result = wf.run()

        assert result["status"] == "completed"
        assert result["total"] == 5
        assert result["indexed"]["papers"] == 2
        assert result["indexed"]["meetings"] == 3
