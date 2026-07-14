from src.managers.base_manager import BaseManager
from src.services.meeting_service import MeetingService
from src.persistence.meeting_repository import MeetingRepository

class MeetingManager(BaseManager):
    def __init__(self, agent=None):
        super().__init__("Meeting Manager", agent=agent)
        self._service: MeetingService | None = None

    def initialize(self):
        super().initialize()
        repo = None
        if self.services:
            repo = self.services.get("meeting_repo")
            if repo is None and self.config:
                db_path = self.config.get("chat.db_path", "./workspace/chat_history.db")
                repo = MeetingRepository(db_path)

        self._service = MeetingService(
            llm_service=self.services.get("llm") if self.services else None,
            prompt_service=self.services.get("prompt") if self.services else None,
            asr_service=self.services.get("asr") if self.services else None,
            meeting_repo=repo,
            knowledge_service=self.services.get("knowledge_service") if self.services else None,
        )

    @property
    def service(self) -> MeetingService | None:
        return self._service

    def transcribe_meeting(self, audio_path: str, title: str = None):
        return self._service.transcribe_meeting(audio_path, title)

    def process_meeting_text(self, text: str, title: str = None):
        return self._service.process_text(text, title)

    def get_meeting(self, meeting_id: str):
        return self._service.get_meeting(meeting_id)

    def list_meetings(self):
        return self._service.list_meetings()

    def delete_meeting(self, meeting_id: str):
        self._service.delete_meeting(meeting_id)

    def generate_weekly_report(self, start_date: str = None, end_date: str = None) -> str:
        return self._service.generate_weekly_report(start_date, end_date)
