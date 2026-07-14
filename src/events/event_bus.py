"""
事件总线模块 - 基于发布/订阅模式的解耦事件系统

EventBus是线程安全的单例，服务通过它发布领域事件，
监听器订阅感兴趣的事件类型并异步响应。
主要用于自动索引：当论文/会议/实验创建时自动索引到知识库。
"""

import logging
from collections import defaultdict

from src.events.event import Event


class EventBus:
    """线程安全的事件总线单例 - 实现发布/订阅模式。

    用于解耦服务间的通信。服务发布领域事件（如 paper.created），
    监听器订阅并响应事件（如自动索引到知识库）。
    这样索引逻辑就不会侵入核心服务代码。

    Attributes:
        _handlers: 事件类型→处理函数列表的映射
        _logger: 日志记录器
    """

    _instance = None

    def __new__(cls):
        """单例模式 - 确保全局只有一个EventBus实例。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = defaultdict(list)
            cls._instance._logger = logging.getLogger("ResearchAgent.EventBus")
        return cls._instance

    def subscribe(self, event_type: str, handler):
        """订阅事件类型。

        Args:
            event_type: 事件类型字符串（如 "paper.created"）
            handler: 事件处理函数，接收Event对象作为参数
        """
        self._handlers[event_type].append(handler)
        self._logger.info(f"Subscribed to '{event_type}': {handler.__name__}")

    def publish(self, event_type: str, data: dict = None, source: str = ""):
        """发布事件，通知所有订阅者。

        Args:
            event_type: 事件类型字符串
            data: 事件数据载荷
            source: 事件来源标识
        """
        event = Event(type=event_type, data=data or {}, source=source)
        handlers = self._handlers.get(event_type, [])
        self._logger.info(f"Event '{event_type}' published, {len(handlers)} handlers")

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # 某个处理器失败不应影响其他处理器
                self._logger.error(f"Handler {handler.__name__} failed for '{event_type}': {e}")

    def clear(self):
        """清空所有事件订阅（主要用于测试）。"""
        self._handlers.clear()
