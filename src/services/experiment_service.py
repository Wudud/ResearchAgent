"""
实验服务模块 - 实验管理的核心服务实现。

提供实验生命周期管理和数据分析功能。
"""

import json
import logging
from datetime import datetime, timezone

from src.services.llm_service import LLMService
from src.persistence.experiment_repository import ExperimentRepository


class ExperimentService:
    """实验服务 - 实验管理的核心业务逻辑。"""

    def __init__(self, llm_service: LLMService = None, prompt_service=None, experiment_repo: ExperimentRepository = None):
        self._llm = llm_service
        self._prompts = prompt_service
        self._repo = experiment_repo
        self._logger = logging.getLogger("ResearchAgent.ExperimentService")

    def create_experiment(self, name: str, dataset: str = "", model: str = "",
                          parameters: dict = None, description: str = "") -> object:
        """创建新实验。"""
        from src.experiment.models import Experiment
        exp = Experiment(
            name=name, dataset=dataset, model=model,
            parameters=parameters, description=description
        )
        return self._repo.create(exp)

    def get_experiment(self, exp_id: int):
        """获取实验。"""
        return self._repo.get(exp_id)

    def list_experiments(self):
        """列出所有实验。"""
        return self._repo.list_all()

    def list_by_status(self, status: str):
        """按状态过滤。"""
        return self._repo.list_by_status(status)

    def delete_experiment(self, exp_id: int):
        """删除实验。"""
        self._repo.delete(exp_id)

    def update_status(self, exp_id: int, status: str):
        """更新实验状态。"""
        valid = {"created", "running", "completed", "failed", "paused"}
        if status not in valid:
            raise ValueError(f"Invalid status: {status}")
        self._repo.update_status(exp_id, status)

    def start_experiment(self, exp_id: int):
        """开始实验。"""
        self._repo.update_status(exp_id, "running")

    def complete_experiment(self, exp_id: int):
        """完成实验。"""
        self._repo.update_status(exp_id, "completed")

    def log_parameters(self, exp_id: int, params: dict):
        """记录实验参数。"""
        exp = self._repo.get(exp_id)
        if exp is None:
            raise ValueError(f"Experiment {exp_id} not found")
        current = dict(exp.parameters) if exp.parameters else {}
        current.update(params)
        self._repo.update(exp_id, parameters=json.dumps(current))

    def log_metrics(self, exp_id: int, step: int = None, **metrics):
        """记录实验指标。"""
        exp = self._repo.get(exp_id)
        if exp is None:
            raise ValueError(f"Experiment {exp_id} not found")
        current = list(exp.metrics) if exp.metrics else []
        entry = {k: v for k, v in metrics.items()}
        if step is not None:
            entry["step"] = step
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        current.append(entry)
        self._repo.update(exp_id, metrics=json.dumps(current))

    def generate_report(self, exp_id: int) -> str:
        """生成实验报告。"""
        exp = self._repo.get(exp_id)
        if exp is None:
            return f"Experiment {exp_id} not found."
        if self._llm is None:
            return self._build_simple_report(exp)
        params = getattr(exp, 'parameters', {}) or {}
        metrics_list = getattr(exp, 'metrics', []) or []
        prompt = f"""Generate an experiment report.

Name: {getattr(exp, 'name', '')}
Dataset: {getattr(exp, 'dataset', '')}
Model: {getattr(exp, 'model', '')}
Parameters: {json.dumps(params)}
Metrics: {json.dumps(metrics_list)}"""
        return self._llm.chat([{"role": "user", "content": prompt}])

    def _build_simple_report(self, exp) -> str:
        """无LLM时的简单报告。"""
        dataset = getattr(exp, 'dataset', '') or ''
        params = getattr(exp, 'parameters', {}) or {}
        params_str = ", ".join(f"{k}={v}" for k, v in params.items())
        return f"# {getattr(exp, 'name', 'Experiment')}\nDataset: {dataset}\nParameters: {params_str}\nStatus: {getattr(exp, 'status', 'N/A')}"

    def compare_experiments(self, exp_ids: list[int]) -> str:
        """对比多个实验。"""
        if len(exp_ids) < 2:
            return "Need at least 2 experiments to compare."
        exps = [self._repo.get(eid) for eid in exp_ids]
        if any(e is None for e in exps):
            return "One or more experiments not found."
        lines = ["# Experiment Comparison\n"]
        for e in exps:
            lines.append(f"- **{e.name}**: {json.dumps(e.metrics)[:200]}")
        return "\n".join(lines)
