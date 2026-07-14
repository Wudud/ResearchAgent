"""
事件监听器模块 - 知识库自动索引的事件监听器

当领域事件（论文/会议/实验创建）发生时，
自动将内容索引到知识库中。
"""

import logging


def create_knowledge_index_listener(knowledge_manager):
    """工厂函数：创建将内容索引到知识库的事件监听器。

    Args:
        knowledge_manager: 知识库管理器实例

    Returns:
        dict: 事件类型→处理函数的映射字典
    """
    logger = logging.getLogger("ResearchAgent.Listeners")

    def on_paper_created(event):
        """论文创建事件处理 - 自动索引论文到知识库。"""
        paper = event.data.get("paper")
        if paper:
            knowledge_manager.index_paper(paper)
            logger.info(f"Auto-indexed paper: {paper.title}")

    def on_meeting_created(event):
        """会议创建事件处理 - 自动索引会议到知识库。"""
        meeting = event.data.get("meeting")
        if meeting:
            knowledge_manager.index_meeting(meeting)
            logger.info(f"Auto-indexed meeting: {meeting.title}")

    def on_experiment_created(event):
        """实验创建事件处理 - 自动索引实验到知识库。"""
        exp = event.data.get("experiment")
        if exp:
            knowledge_manager.index_experiment(exp)
            logger.info(f"Auto-indexed experiment: {exp.name}")

    return {
        "paper.created": on_paper_created,
        "meeting.created": on_meeting_created,
        "experiment.created": on_experiment_created,
    }


def register_knowledge_listeners(event_bus, knowledge_manager):
    """在EventBus上注册所有知识库相关的监听器。

    Args:
        event_bus: 事件总线实例
        knowledge_manager: 知识库管理器实例
    """
    listeners = create_knowledge_index_listener(knowledge_manager)
    for event_type, handler in listeners.items():
        event_bus.subscribe(event_type, handler)
