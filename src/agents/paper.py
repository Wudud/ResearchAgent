"""
论文Agent模块 - 专门处理论文分析和管理任务的智能Agent。

提供论文导入、分析、引用管理和文献综述生成等功能。
通过ReAct循环将用户目标分解为论文管理工具调用序列。
"""

from src.agents.base import BaseAgent


class PaperAgent(BaseAgent):
    """论文Agent - 将论文管理操作封装为LLM可调用的工具。

    注册的工具包括：导入论文、提取引用、生成摘要和列出论文。

    Attributes:
        _manager: PaperManager实例
    """

    def __init__(self, manager, reasoning_service, persona_prompt: str = ""):
        """初始化论文Agent。

        Args:
            manager: PaperManager实例
            reasoning_service: 推理服务
            persona_prompt: 角色提示词
        """
        persona = persona_prompt or "你是一个论文分析专家。请使用提供的工具分析和处理论文。"
        super().__init__("PaperAgent", manager, reasoning_service, persona)

    def _register_tools(self):
        """注册论文管理相关的工具。"""
        self._add_tool("ingest_paper", "导入论文",
                       lambda file_path: self._manager.ingest_paper(file_path))
        self._add_tool("extract_citations", "提取引用",
                       lambda paper_id: self._manager.extract_citations(paper_id))
        self._add_tool("summarize_paper", "生成论文摘要",
                       lambda paper_id: self._manager.summarize_paper(paper_id))
        self._add_tool("list_papers", "列出所有论文",
                       lambda: self._manager.list_papers())
