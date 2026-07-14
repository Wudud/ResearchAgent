"""
任务模型模块 - 定义任务管理的核心数据结构。

包含任务定义、状态枚举和依赖关系等Pydantic/dataclass模型。
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    """任务数据类 - 表示一个待办任务。

    Attributes:
        id: 任务ID
        content: 任务内容描述
        priority: 优先级（high/medium/low）
        status: 任务状态
        source: 来源（Meeting/Paper/Assistant/Experiment）
        deadline: 截止日期
        created_at: 创建时间
        completed_at: 完成时间
    """
    id: int | None = None
    content: str = ""
    priority: str = "medium"
    status: str = "pending"
    source: str = ""
    deadline: str = ""
    created_at: str = ""
    completed_at: str = ""
