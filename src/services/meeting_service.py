import json
import logging
from datetime import datetime, timezone

from src.meeting.models import Meeting
from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService
from src.services.asr_service import ASRService
from src.persistence.meeting_repository import MeetingRepository

class MeetingService:
    def __init__(
        self,
        llm_service: LLMService = None,
        prompt_service: PromptService = None,
        asr_service: ASRService = None,
        meeting_repo: MeetingRepository = None,
        knowledge_service = None,
    ):
        self._llm = llm_service
        self._prompts = prompt_service
        self._asr = asr_service
        self._repo = meeting_repo
        self._knowledge = knowledge_service
        self._logger = logging.getLogger("ResearchAgent.MeetingService")

    # --- Main workflow ---

    def transcribe_meeting(self, audio_path: str, title: str = None) -> Meeting:
        if self._asr is None or not self._asr.available:
            raise RuntimeError("ASR 服务未配置，无法转写音频。")

        self._logger.info(f"Transcribing meeting: {audio_path}")
        transcript = self._asr.transcribe(audio_path)

        if title is None:
            title = f"会议 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        meeting = Meeting(
            id="",
            title=title,
            transcript=transcript,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        meeting = self._repo.save(meeting)
        self._logger.info(f"Meeting created: {meeting.id}")

        self._analyze(meeting.id)
        meeting = self._repo.get(meeting.id)
        self._publish("meeting.created", {"meeting": meeting})
        return meeting

    def process_text(self, text: str, title: str = None) -> Meeting:
        if title is None:
            title = f"会议 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        meeting = Meeting(
            id="",
            title=title,
            transcript=text,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        meeting = self._repo.save(meeting)
        self._analyze(meeting.id)
        meeting = self._repo.get(meeting.id)

        meeting = self._repo.get(meeting.id)
        self._publish("meeting.created", {"meeting": meeting})
        return meeting

    def _publish(self, event_type: str, data: dict):
        try:
            from src.events.event_bus import EventBus
            EventBus().publish(event_type, data, source="MeetingService")
        except Exception:
            pass

    # --- Analysis ---

    def _analyze(self, meeting_id: str):
        if self._llm is None:
            return

        meeting = self._repo.get(meeting_id)
        if meeting is None or not meeting.transcript:
            return

        self._logger.info(f"Analyzing meeting: {meeting_id}")
        prompt = self._prompts.render("meeting/meeting_analysis.md", transcript=meeting.transcript)
        messages = [{"role": "user", "content": prompt}]
        response = self._llm.chat(messages)

        try:
            data = self._parse_json(response)
            meeting.summary = data.get("summary", "")
            meeting.discussion = data.get("discussion", "")
            meeting.decision = data.get("decision", "")
            meeting.suggestions = data.get("suggestions", [])
            meeting.next_step = data.get("next_step", "")
            meeting._tasks = data.get("tasks", [])
        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(f"Failed to parse meeting analysis JSON: {e}")
            meeting.summary = response
            meeting._tasks = []

        self._repo.save(meeting)

    def _parse_json(self, raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = lines[1:] if len(lines) > 1 else lines
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines)
        return json.loads(raw)

    # --- Accessors ---

    def generate_summary(self, meeting_id: str) -> str:
        m = self._repo.get(meeting_id)
        return m.summary if m else ""

    def extract_suggestions(self, meeting_id: str) -> list[str]:
        m = self._repo.get(meeting_id)
        return m.suggestions if m else []

    def extract_tasks(self, meeting_id: str) -> list[dict]:
        m = self._repo.get(meeting_id)
        if m is None:
            return []

        if self._llm is None:
            return []

        prompt = self._prompts.render("meeting/meeting_analysis.md", transcript=m.transcript)
        messages = [{"role": "user", "content": prompt}]
        response = self._llm.chat(messages)

        try:
            data = self._parse_json(response)
            return data.get("tasks", [])
        except Exception:
            return []

    def update_memory(self, meeting_id: str):
        if self._knowledge is None or not self._knowledge.available:
            return
        meeting = self._repo.get(meeting_id)
        if meeting is None:
            return
        text = f"标题: {meeting.title or '未命名'}\n摘要: {meeting.summary or ''}\n"
        if meeting.suggestions:
            text += "导师建议: " + "; ".join(meeting.suggestions) + "\n"
        if meeting.next_step:
            text += "下一步: " + meeting.next_step + "\n"
        if meeting.decision:
            text += "决定: " + meeting.decision + "\n"
        self._knowledge.index_text("meeting", text, {
            "title": meeting.title or "未命名",
            "id": meeting.id or "",
            "date": meeting.created_at or "",
        })

    # --- Report ---

    def list_meetings(self):
        return self._repo.list_all()

    def get_meeting(self, meeting_id: str):
        return self._repo.get(meeting_id)

    def delete_meeting(self, meeting_id: str):
        self._repo.delete(meeting_id)

    def generate_weekly_report(self, start_date: str = None, end_date: str = None) -> str:
        meetings = self._repo.list_all()
        if not meetings:
            return "本周暂无会议记录。"

        if self._llm is None:
            return self._build_simple_report(meetings)

        summaries = []
        for m in meetings:
            summaries.append(f"## {m.title}\n\n{m.summary}\n\n待办: {len(getattr(m, '_tasks', []))} 项")

        report_text = "\n\n".join(summaries)
        prompt = f"""请基于以下本周会议内容，生成一份科研周报。

要求：
1. Markdown 格式
2. 包含：工作进展、TODO完成情况、下周计划、需要讨论的问题
3. 中文输出

本周会议内容：
{report_text}"""
