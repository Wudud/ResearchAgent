"""
实验Agent模块 - 专门处理实验管理任务的智能Agent。

提供实验创建、运行、状态追踪和结果分析等功能。
通过ReAct循环将用户目标分解为实验管理工具调用序列。
"""

from src.agents.base import BaseAgent


class ExperimentAgent(BaseAgent):
    """实验Agent - 将实验管理操作封装为LLM可调用的工具。

    注册的工具包括：创建实验、运行实验、列出实验和获取实验状态。

    Attributes:
        _manager: ExperimentManager实例
    """

    def __init__(self, manager, reasoning_service, persona_prompt: str = ""):
        """初始化实验Agent。

        Args:
            manager: ExperimentManager实例
            reasoning_service: 推理服务
            persona_prompt: 角色提示词
        """
        persona = persona_prompt or "你是一个实验分析专家。请使用提供的工具完成实验相关任务。"
        super().__init__("ExperimentAgent", manager, reasoning_service, persona)

    def _register_tools(self):
        """注册实验管理相关的工具。"""
        self._add_tool("create_experiment", "创建新实验",
                       lambda name, dataset_id="", config=None: self._manager.create_experiment(name, dataset_id, config))
        self._add_tool("run_experiment", "运行实验",
                       lambda experiment_id: self._manager.run_experiment(experiment_id))
        self._add_tool("list_experiments", "列出所有实验",
                       lambda: self._manager.list_experiments())
        self._add_tool("get_experiment_status", "获取实验状态",
                       lambda experiment_id: self._manager.get_experiment_status(experiment_id))
        self._add_tool("generate_report", "生成实验报告",
                       lambda experiment_id: self._manager.generate_report(experiment_id))
        self._add_tool("update_experiment", "更新实验状态",
                       lambda experiment_id, status, metrics=None: self._manager.update_status(experiment_id, status, metrics))
