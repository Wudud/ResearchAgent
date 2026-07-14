"""
报告服务模块 - 自动生成研究分析报告。

使用LLM按模板生成结构化Markdown报告，
支持周报生成和简单文本报告两种模式。
"""

import logging

from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService


class ReportService:
    """报告服务 - 生成格式化的研究分析报告。

    LLM可用时生成高质量结构化报告，不可用时回退到简单的文本拼装。

    Attributes:
        _llm: LLM服务实例
        _prompts: 提示词服务
    """

    def __init__(self, llm_service: LLMService = None, prompt_service: PromptService = None):
        self._llm = llm_service
        self._prompts = prompt_service
        self._logger = logging.getLogger("ResearchAgent.ReportService")

    def generate_weekly_report(self, meeting_summaries: list[str], todo_stats: dict) -> str:
        """生成科研周报。

        Args:
            meeting_summaries: 本周会议摘要列表
            todo_stats: TODO任务统计 {"total": N, "completed": N, "in_progress": N}

        Returns:
            str: Markdown格式的周报
        """
        if self._llm is None:
            return self._build_simple_weekly(meeting_summaries, todo_stats)

        meetings_text = "\n\n".join(meeting_summaries) if meeting_summaries else "本周暂无会议。"
        prompt = f"""请基于以下内容生成一份科研周报。

要求：
1. Markdown 格式，中文输出
2. 包含：工作进展、TODO完成情况、下周计划、需要讨论的问题
3. 语言简洁，每条 1-2 句话

本周会议内容：
{meetings_text}

TODO 统计：
- 总任务: {todo_stats.get('total', 0)}
- 已完成: {todo_stats.get('completed', 0)}
- 进行中: {todo_stats.get('in_progress', 0)}"""
        messages = [{"role": "user", "content": prompt}]
        return self._llm.chat(messages)

    def _build_simple_weekly(self, summaries: list[str], stats: dict) -> str:
        """LLM不可用时的简单周报拼装。

        Args:
            summaries: 会议摘要列表
            stats: TODO统计数据

        Returns:
            str: 简单文本格式的周报
        """
        lines = ["# 本周工作总结\n"]
        for s in summaries:
            lines.append(s)
            lines.append("")
        lines.append(f"## TODO 统计")
        lines.append(f"- 已完成: {stats.get('completed', 0)}")
        lines.append(f"- 进行中: {stats.get('in_progress', 0)}")
        return "\n".join(lines)
