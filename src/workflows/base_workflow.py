"""
工作流基类模块 - 定义多步骤工作流的抽象框架。

提供步骤定义、执行顺序和错误恢复的通用逻辑。
各领域工作流继承此类，实现各自的步骤序列。
"""

import logging


class BaseWorkflow:
    """工作流基类 - 定义多步骤研究流程的通用框架。

    每个具体的工作流（论文、会议、实验、数据集等）继承此类，
    实现各自的execute()方法来定义具体的处理步骤。

    Attributes:
        name: 工作流名称
        agent: ResearchAgent实例
        _logger: 日志记录器
    """

    def __init__(self, name: str, agent):
        """初始化工作流。

        Args:
            name: 工作流名称标识
            agent: ResearchAgent实例
        """
        self.name = name
        self.agent = agent
        self._logger = logging.getLogger(f"ResearchAgent.Workflow.{name}")

    def run(self, **kwargs) -> dict:
        """执行工作流主流程（别名）。子类必须重写此方法。"""
        return self.execute(**kwargs)

    def execute(self, **kwargs) -> dict:
        """执行工作流主流程。子类必须重写此方法。

        Raises:
            NotImplementedError: 子类未实现时抛出
        """
        raise NotImplementedError("Subclass must implement execute()")

    def validate_inputs(self, **kwargs) -> bool:
        """验证工作流输入参数。子类可重写以添加特定验证。

        Args:
            **kwargs: 待验证的参数

        Returns:
            bool: 参数有效返回True
        """
        return True

    def cleanup(self):
        """工作流执行后的清理操作。子类可重写以释放资源。"""
        pass
