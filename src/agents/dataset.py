"""
数据集Agent模块 - 专门处理数据集管理任务的智能Agent。

提供数据集扫描、统计、去重、完整性检查和报告生成等功能。
通过ReAct循环将用户目标分解为工具调用序列。
"""

from src.agents.base import BaseAgent


class DatasetAgent(BaseAgent):
    """数据集Agent - 将数据集管理操作封装为LLM可调用的工具。

    注册的工具包括：扫描数据集、完整性检查、统计信息、
    报告生成和Dataset Card生成。

    Attributes:
        _manager: DatasetManager实例
    """

    def __init__(self, manager, reasoning_service, persona_prompt: str = ""):
        """初始化数据集Agent。

        Args:
            manager: DatasetManager实例
            reasoning_service: 推理服务
            persona_prompt: 角色提示词
        """
        persona = persona_prompt or "你是一个数据集管理专家。请使用提供的工具完成数据集相关任务。"
        super().__init__("DatasetAgent", manager, reasoning_service, persona)

    def _register_tools(self):
        """注册数据集管理相关的工具。"""
        self._add_tool("scan_dataset", "扫描数据集目录",
                       lambda root_path=None: self._manager.scan_dataset(root_path))
        self._add_tool("check_integrity", "检查数据集完整性",
                       lambda manifest_path=None: self._manager.check_integrity(manifest_path))
        self._add_tool("get_statistics", "获取数据集统计信息",
                       lambda: self._manager.get_statistics())
        self._add_tool("generate_report", "生成数据集报告",
                       lambda dataset_name=None: self._manager.generate_report(dataset_name))
        self._add_tool("generate_dataset_card", "生成 Dataset Card",
                       lambda dataset_name=None, version="1.0.0": self._manager.generate_dataset_card(dataset_name, version))
