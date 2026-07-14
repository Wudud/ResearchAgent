import json
from unittest.mock import MagicMock

import pytest

from src.experiment.models import Experiment
from src.persistence.experiment_repository import ExperimentRepository
from src.services.experiment_service import ExperimentService
from src.services.llm_service import LLMService

class TestExperimentModel:
    def test_create_experiment_defaults(self):
        exp = Experiment(name="Test")
        assert exp.parameters == {}
        assert exp.metrics == []
        assert exp.id is None

    def test_create_experiment_full(self):
        exp = Experiment(
            id=1,
            name="Exp01",
            dataset="DairySheepHR",
            model="PointNet++",
            parameters={"lr": 0.001, "epochs": 100},
            metrics=[{"step": 0, "loss": 0.5}],
            log_path="./logs/exp01",
            checkpoint_path="./ckpt/exp01",
            tensorboard_path="./runs/exp01",
        )
        assert exp.id == 1
        assert exp.dataset == "DairySheepHR"
        assert exp.model == "PointNet++"
        assert exp.parameters["lr"] == 0.001
        assert len(exp.metrics) == 1

class TestExperimentRepository:
    @pytest.fixture
    def repo(self):
        return ExperimentRepository(":memory:")

    def test_create(self, repo):
        exp = Experiment(name="Exp01", dataset="DS", model="PN")
        result = repo.create(exp)
        assert result.id == 1
        assert result.created_at != ""

    def test_get(self, repo):
        exp = repo.create(Experiment(name="Exp01"))
        fetched = repo.get(exp.id)
        assert fetched is not None
        assert fetched.name == "Exp01"

    def test_get_nonexistent(self, repo):
        assert repo.get(999) is None

    def test_list_all(self, repo):
        repo.create(Experiment(name="E1"))
        repo.create(Experiment(name="E2"))
        all_exps = repo.list_all()
        assert len(all_exps) == 2
        names = {e.name for e in all_exps}
        assert names == {"E1", "E2"}

    def test_list_by_status(self, repo):
        repo.create(Experiment(name="E1", status="created"))
        repo.create(Experiment(name="E2", status="active"))
        active = repo.list_by_status("active")
        assert len(active) == 1
        assert active[0].name == "E2"

    def test_update(self, repo):
        exp = repo.create(Experiment(name="Old"))
        exp.name = "New"
        exp.parameters = {"lr": 0.01}
        repo.update(exp)
        fetched = repo.get(exp.id)
        assert fetched.name == "New"
        assert fetched.parameters == {"lr": 0.01}

    def test_update_status(self, repo):
        exp = repo.create(Experiment(name="E1"))
        repo.update_status(exp.id, "completed")
        fetched = repo.get(exp.id)
        assert fetched.completed_at != ""

    def test_delete(self, repo):
        exp = repo.create(Experiment(name="E1"))
        repo.delete(exp.id)
        assert repo.get(exp.id) is None

    def test_json_serialization(self, repo):
        exp = repo.create(Experiment(
            name="E1",
            parameters={"n_layers": 3, "dropout": 0.5},
            metrics=[{"step": 0, "loss": 1.0}, {"step": 1, "loss": 0.5}],
        ))
        fetched = repo.get(exp.id)
        assert fetched.parameters == {"n_layers": 3, "dropout": 0.5}
        assert len(fetched.metrics) == 2
        assert fetched.metrics[0]["loss"] == 1.0

class TestExperimentService:
    @pytest.fixture
    def repo(self):
        return ExperimentRepository(":memory:")

    @pytest.fixture
    def mock_llm(self):
        svc = MagicMock(spec=LLMService)
        return svc

    @pytest.fixture
    def service(self, repo):
        return ExperimentService(experiment_repo=repo)

    @pytest.fixture
    def service_with_llm(self, repo, mock_llm):
        return ExperimentService(llm_service=mock_llm, experiment_repo=repo)

    def test_create_experiment(self, service):
        exp = service.create_experiment(
            name="Exp01", dataset="DS", model="PN",
            parameters={"lr": 0.001},
        )
        assert exp.id == 1
        assert exp.parameters == {"lr": 0.001}

    def test_log_parameters(self, service):
        exp = service.create_experiment(name="Exp01")
        service.log_parameters(exp.id, {"batch_size": 32})
        fetched = service.get_experiment(exp.id)
        assert fetched.parameters == {"batch_size": 32}

    def test_log_parameters_merge(self, service):
        exp = service.create_experiment(name="Exp01", parameters={"lr": 0.001})
        service.log_parameters(exp.id, {"epochs": 100})
        fetched = service.get_experiment(exp.id)
        assert fetched.parameters == {"lr": 0.001, "epochs": 100}

    def test_log_parameters_nonexistent(self, service):
        with pytest.raises(ValueError, match="not found"):
            service.log_parameters(999, {"lr": 0.001})

    def test_log_metrics(self, service):
        exp = service.create_experiment(name="Exp01")
        service.log_metrics(exp.id, step=0, loss=1.0, mae=0.5)
        fetched = service.get_experiment(exp.id)
        assert len(fetched.metrics) == 1
        assert fetched.metrics[0]["loss"] == 1.0
        assert fetched.metrics[0]["mae"] == 0.5
        assert fetched.metrics[0]["step"] == 0
        assert "timestamp" in fetched.metrics[0]

    def test_log_metrics_multiple(self, service):
        exp = service.create_experiment(name="Exp01")
        service.log_metrics(exp.id, step=0, loss=1.0)
        service.log_metrics(exp.id, step=1, loss=0.7)
        service.log_metrics(exp.id, step=2, loss=0.3)
        fetched = service.get_experiment(exp.id)
        assert len(fetched.metrics) == 3
        assert fetched.metrics[2]["loss"] == 0.3

    def test_update_status_invalid(self, service):
        exp = service.create_experiment(name="Exp01")
        with pytest.raises(ValueError, match="Invalid status"):
            service.update_status(exp.id, "invalid_status")

    def test_start_and_complete(self, service):
        exp = service.create_experiment(name="Exp01")
        service.start_experiment(exp.id)
        service.complete_experiment(exp.id)
        fetched = service.get_experiment(exp.id)
        assert fetched.completed_at != ""

    def test_generate_report_no_llm(self, service):
        exp = service.create_experiment(name="Exp01", dataset="DS", parameters={"lr": 0.01})
        service.log_metrics(exp.id, step=0, loss=1.0)
        report = service.generate_report(exp.id)
        assert "Exp01" in report
        assert "DS" in report
        assert "lr" in report

    def test_generate_report_with_llm(self, service_with_llm):
        exp = service_with_llm.create_experiment(name="Exp01")
        report = service_with_llm.generate_report(exp.id)

    def test_generate_report_nonexistent(self, service):
        report = service.generate_report(999)

    def test_compare_experiments(self, service_with_llm):
        e1 = service_with_llm.create_experiment(name="E1", dataset="DS1", parameters={"lr": 0.001})
        e2 = service_with_llm.create_experiment(name="E2", dataset="DS2", parameters={"lr": 0.01})
        service_with_llm.log_metrics(e1.id, step=0, loss=1.0)
        service_with_llm.log_metrics(e2.id, step=0, loss=0.5)
        report = service_with_llm.compare_experiments([e1.id, e2.id])

    def test_compare_empty(self, service):
        report = service.compare_experiments([])

    def test_list_and_delete(self, service):
        e1 = service.create_experiment(name="E1")
        e2 = service.create_experiment(name="E2")
        assert len(service.list_experiments()) == 2
        service.delete_experiment(e1.id)
        assert len(service.list_experiments()) == 1
        assert service.get_experiment(e1.id) is None

    def test_list_by_status(self, service):
        e1 = service.create_experiment(name="E1")
        service.complete_experiment(e1.id)
        e2 = service.create_experiment(name="E2")
        assert len(service.list_experiments()) == 2
