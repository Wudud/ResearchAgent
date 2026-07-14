"""
工具基类模块 - 定义所有工具的抽象接口和通用行为。

提供参数验证、错误处理和结果格式化等基础功能。
所有具体工具必须继承此基类并实现抽象方法。
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """工具抽象基类 - 定义工具的标准化接口。

    每个具体工具必须实现name、description属性和run方法。

    Attributes:
        name: 工具名称标识
        description: 工具功能描述
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """返回工具名称。

        Returns:
            str: 工具的唯一名称标识
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """返回工具功能描述。

        Returns:
            str: 工具的功能说明文本
        """
        ...

    @abstractmethod
    def run(self, **kwargs):
        """执行工具的主方法。

        Args:
            **kwargs: 工具执行所需的具体参数

        Returns:
            工具执行的结果，类型取决于具体实现
        """
        ...
