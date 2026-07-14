"""
管理器守卫组件 - 检查管理器状态的条件渲染组件。

在管理器未就绪时显示友好的提示信息，
确保页面在所需服务可用时才渲染功能区域。
"""

from streamlit import error as _error, warning as _warning
from typing import Optional


def check_manager(agent, manager_name: str) -> bool:
    """检查指定管理器是否可用。

    Args:
        agent: ResearchAgent实例
        manager_name: 管理器名称

    Returns:
        bool: 管理器可用返回True，否则显示错误信息并返回False
    """
    if agent is None:
        _error("System not initialized. Please check your configuration.")
        return False

    manager = agent.managers.get(manager_name)
    if manager is None:
        _error(f"Manager '{manager_name}' is not available. Please check your configuration.")
        return False

    return True
