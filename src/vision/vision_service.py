"""
视觉服务模块 - 图像分析的统一服务层。

支持图像描述、问答和视觉推理等高级功能。
在基础视觉适配器之上提供统一的图像分析接口。
"""

import logging

from src.vision.vision_adapter import BaseVisionAdapter, VisionResult


class VisionService:
    """视觉服务 - 图像分析的统一服务入口。

    封装视觉适配器，提供图像理解和描述的标准化接口。
    支持在模型不可用时优雅降级。

    Attributes:
        _adapter: 视觉适配器实例
        _logger: 日志记录器
    """

    def __init__(self, adapter: BaseVisionAdapter = None):
        """初始化视觉服务。

        Args:
            adapter: 视觉适配器实例，为None时服务不可用
        """
        self._adapter = adapter
        self._logger = logging.getLogger("ResearchAgent.VisionService")

    @property
    def provider(self) -> str:
        """获取当前视觉提供商名称。

        Returns:
            str: 提供商名称，适配器不可用时返回"none"
        """
        if self._adapter:
            return self._adapter.provider
        return "none"

    @property
    def available(self) -> bool:
        """检查视觉服务是否可用。

        Returns:
            bool: 适配器存在且可用时返回True
        """
        return self._adapter is not None

    def analyze(self, image_path: str, prompt: str = "") -> VisionResult:
        """分析图像并返回描述结果。"""
        if not self.available:
            return VisionResult(description="Vision service not configured")
        return self._adapter.analyze(image_path)

    def describe(self, image_path: str) -> str:
        """生成图像的简单文字描述。

        Args:
            image_path: 图像文件路径

        Returns:
            str: 图像描述文本，服务不可用时返回空字符串
        """
        if not self.available:
            return ""
        result = self._adapter.analyze(image_path)
        text = result.description if result else ""
        if result and result.ocr_text:
            text += "\n" + result.ocr_text
        return text

    def ocr(self, image_path: str) -> str:
        """提取图像中的文字。

        Args:
            image_path: 图像文件路径

        Returns:
            str: OCR提取的文字
        """
        if not self.available:
            return ""
        result = self._adapter.analyze(image_path)
        return result.ocr_text if result else ""
