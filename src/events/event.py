"""
事件数据模型 - 定义系统中传递的事件数据结构

使用dataclass简化事件对象的创建和管理，
事件包含类型、数据载荷、时间戳和来源信息。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Event:
    """事件数据类 - 表示系统中的一个领域事件。

    Attributes:
        type: 事件类型标识（如 "paper.created", "meeting.created"）
        data: 事件携带的数据载荷
        timestamp: ISO格式的UTC时间戳，自动生成
        source: 事件来源标识
    """
    type: str
    data: dict = field(default_factory=dict)
    timestamp: str = ""
    source: str = ""

    def __post_init__(self):
        """初始化后处理 - 自动设置时间戳。"""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
