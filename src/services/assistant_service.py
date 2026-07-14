"""
助手服务模块 - 对话助手的核心服务实现。

支持多轮对话、RAG上下文检索和工具调用增强。
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService
from src.services.asr_service import ASRService
from src.tools.file_readers.router import FileRouter
from src.persistence.conversation_repository import ConversationRepository
from src.assistant.message import Message


class AssistantService:
    """助手服务 - 对话助手核心业务逻辑。

    管理多轮对话、文件问答和知识库增强回复。

    Attributes:
        _llm: LLM服务
        _prompts: 提示词服务
        _asr: 语音识别服务
        _router: 文件路由器
        _repo: 对话仓库
        _knowledge: 知识库服务
        _context_window: 上下文窗口大小
    """

    def __init__(
        self,
        llm_service: LLMService = None,
        prompt_service: PromptService = None,
        asr_service: ASRService = None,
        repo: ConversationRepository = None,
        conversation_repo: ConversationRepository = None,
        knowledge_service=None,
        context_window: int = 20,
    ):
        self._llm = llm_service
        self._prompts = prompt_service
        self._asr = asr_service
        self._router = FileRouter()
        self._repo = repo or conversation_repo
        self._knowledge = knowledge_service
        self._context_window = context_window
        self._logger = logging.getLogger("ResearchAgent.AssistantService")

    def create_conversation(self, title: str = "") -> str:
        """创建新对话。

        Args:
            title: 对话标题

        Returns:
            str: 新对话ID
        """
        conv_id = self._repo.create_conversation(title)
        if title and self._repo.get_conversation(conv_id):
            self._repo.update_title(conv_id, title)
        return conv_id

    def process_text(self, conv_id: str, text: str, attachments: list = None) -> str:
        """处理用户文本消息并获取回复（别名）。"""
        return self.send_message(conv_id, text, attachments)

    def process_audio(self, conv_id: str, audio_path: str) -> str:
        """处理音频文件并获取回复。

        Args:
            conv_id: 对话ID
            audio_path: 音频文件路径

        Returns:
            str: 助手回复
        """
        if self._asr is None or not self._asr.available:
            return "ASR service not available."
        transcript = self._asr.transcribe(audio_path)
        return self.send_message(conv_id, transcript)

    def send_message(self, conv_id: str, content: str, attachments: list = None) -> str:
        """发送用户消息并获取助手回复。

        Args:
            conv_id: 对话ID
            content: 用户消息内容
            attachments: 附件列表

        Returns:
            str: 助手回复文本
        """
        self._repo.add_message(conv_id, "user", content,
                               attachments=attachments or [])

        # 从知识库检索相关上下文
        knowledge_ctx, citations = self._retrieve_knowledge(content)
        response = self._chat(conv_id, knowledge_ctx, citations)

        self._repo.add_message(conv_id, "assistant", response)
        return response

    def process_file(self, conv_id: str, file_path: str) -> str:
        """处理用户上传的文件并生成回复。

        Args:
            conv_id: 对话ID
            file_path: 文件路径

        Returns:
            str: 基于文件内容的助手回复
        """
        doc = self._router.route(file_path)
        file_content = doc.content[:8000] if len(doc.content) > 8000 else doc.content
        file_name = Path(file_path).name
        prompt = f"用户上传了文件: {file_name}\n\n文件内容:\n{file_content}\n\n请帮助用户理解和分析这个文件的内容。"
        return self.send_message(conv_id, prompt)

    def _retrieve_knowledge(self, query: str) -> tuple[str, str]:
        """从知识库检索相关上下文。"""
        if self._knowledge is None or not self._knowledge.available:
            return "", ""
        try:
            result = self._knowledge.search(query, top_k=5)
            if not result:
                return "", ""
            if isinstance(result, dict):
                return result.get("context", ""), result.get("citations", "")
            if isinstance(result, list):
                context_parts = []
                citation_parts = []
                for i, r in enumerate(result, 1):
                    context_parts.append(f"[{i}] {r.get('content', '')[:500]}")
                    citation_parts.append(f"[{i}] {r.get('source', 'Unknown')}")
                return "\n\n".join(context_parts), "\n".join(citation_parts)
            return str(result), ""
        except Exception as e:
            self._logger.warning(f"Knowledge retrieval failed: {e}")
            return "", ""

    def _chat(self, conv_id: str, knowledge_context: str = "", citations: str = "") -> str:
        """执行LLM对话。

        Args:
            conv_id: 对话ID
            knowledge_context: 知识库检索的上下文
            citations: 引用信息

        Returns:
            str: LLM回复文本
        """
        if self._llm is None:
            return "LLM service not configured."

        history = self._repo.get_messages(conv_id)
        system_prompt = self._build_system_prompt()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if knowledge_context:
            knowledge_prompt = f"""The following is relevant information from the knowledge base:

{knowledge_context}

---
Please cite relevant sources when answering."""
            messages.append({"role": "system", "content": knowledge_prompt})

        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Apply context window limit
        if self._context_window and len(messages) > self._context_window:
            system_msgs = [m for m in messages if m["role"] == "system"]
            other_msgs = [m for m in messages if m["role"] != "system"]
            messages = system_msgs + other_msgs[-(self._context_window - len(system_msgs)):]

        response = self._llm.chat(messages)

        if citations:
            response = response + "\n\n**References:**\n" + citations

        return response

    def _build_system_prompt(self) -> str:
        """构建系统提示词。

        Returns:
            str: 系统角色提示词
        """
        return "You are a helpful research assistant. Answer questions accurately and concisely."

    def get_conversation(self, conv_id: str) -> dict | None:
        """获取对话信息。

        Args:
            conv_id: 对话ID

        Returns:
            dict: 对话数据
        """
        return self._repo.get_conversation(conv_id)

    def get_messages(self, conv_id: str) -> list[dict]:
        """获取对话的所有消息。

        Args:
            conv_id: 对话ID

        Returns:
            list[dict]: 消息列表
        """
        return self._repo.get_messages(conv_id)

    def list_conversations(self) -> list[dict]:
        """列出所有对话。

        Returns:
            list[dict]: 对话列表
        """
        return self._repo.list_conversations()

    def delete_conversation(self, conv_id: str):
        """删除对话。

        Args:
            conv_id: 对话ID
        """
        self._repo.delete_conversation(conv_id)
