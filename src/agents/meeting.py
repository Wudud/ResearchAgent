"""
会议Agent模块 - 专门处理会议记录和分析的智能Agent。

提供会议创建、音频转录、摘要生成和行动项提取等功能。
通过ReAct循环将用户目标分解为会议管理工具调用序列。
"""

from src.agents.base import BaseAgent


class MeetingAgent(BaseAgent):
    """会议Agent - 将会议管理操作封装为LLM可调用的工具。

    注册的工具包括：创建会议、转录音频、生成摘要和列出会议。

    Attributes:
        _manager: MeetingManager实例
    """

    def __init__(self, manager, reasoning_service, persona_prompt: str = ""):
        """初始化会议Agent。

        Args:
            manager: MeetingManager实例
            reasoning_service: 推理服务
            persona_prompt: 角色提示词
        """
        persona = persona_prompt or "你是一个会议分析专家。请使用提供的工具分析会议内容。"
        super().__init__("MeetingAgent", manager, reasoning_service, persona)

    def _register_tools(self):
        """注册会议管理相关的工具。"""
        self._add_tool("create_meeting", "创建新会议",
                       lambda title, date="", participants=None: self._manager.create_meeting(title, date, participants))
        self._add_tool("transcribe_meeting", "转录会议音频",
                       lambda meeting_id, audio_path=None: self._manager.transcribe_meeting(meeting_id, audio_path))
        self._add_tool("summarize_meeting", "生成会议摘要",
                       lambda meeting_id: self._manager.summarize_meeting(meeting_id))
        self._add_tool("list_meetings", "列出所有会议",
                       lambda: self._manager.list_meetings())
