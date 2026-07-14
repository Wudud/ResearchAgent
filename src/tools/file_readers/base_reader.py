"""
文件读取器基类模块 - 定义所有文件读取器的统一接口。

提供文件的读取、解析和元数据提取标准流程。
支持通过扩展名自动匹配对应的读取器。
"""

from abc import abstractmethod

from src.tools.base_tool import BaseTool


class BaseFileReader(BaseTool):
    """文件读取器基类 - 定义文件解析的统一接口。

    所有具体文件读取器（PDF、DOCX、Markdown等）继承此类，
    实现supported_extensions属性和read方法。

    Attributes:
        supported_extensions: 支持的文件扩展名列表
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """返回支持的文件扩展名列表。

        Returns:
            list[str]: 扩展名列表，如 ['.pdf', '.txt']
        """
        ...

    @abstractmethod
    def read(self, file_path: str) -> str:
        """读取并解析文件内容。

        Args:
            file_path: 文件路径

        Returns:
            str: 解析后的文本内容
        """
        ...

    def can_handle(self, extension: str) -> bool:
        """检查是否能处理指定扩展名的文件。

        Args:
            extension: 文件扩展名

        Returns:
            bool: 能处理返回True
        """
        return extension.lower() in self.supported_extensions

    def run(self, **kwargs):
        """执行文件读取操作。

        Args:
            **kwargs: 必须包含file_path参数

        Returns:
            str: 文件解析结果
        """
        return self.read(kwargs["file_path"])
