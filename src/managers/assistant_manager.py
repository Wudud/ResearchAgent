from src.managers.base_manager import BaseManager
from src.services.assistant_service import AssistantService
from src.assistant.conversation import Conversation
from src.assistant.message import Message

class AssistantManager(BaseManager):
    def __init__(self, agent=None):
        super().__init__("Assistant Manager", agent=agent)
        self._service: AssistantService | None = None

    def initialize(self):
        super().initialize()
        llm = self.services.get("llm") if self.services else None
        prompts = self.services.get("prompt") if self.services else None
        asr = self.services.get("asr") if self.services else None
        repo = self.services.get("conversation_repo") if self.services else None
        knowledge = self.services.get("knowledge_service") if self.services else None
        ctx = self.config.get("chat.context_window", 20) if self.config else 20

        self._service = AssistantService(
            llm_service=llm,
            prompt_service=prompts,
            asr_service=asr,
            repo=repo,
            context_window=ctx,
            knowledge_service=knowledge,
        )

    @property
    def service(self) -> AssistantService | None:
        return self._service

    # --- Delegated methods ---

        return self._service.create_conversation(title)

    def list_conversations(self):
        return self._service.list_conversations()

    def get_conversation(self, conv_id: str):
        return self._service.get_conversation(conv_id)

    def delete_conversation(self, conv_id: str):
        self._service.delete_conversation(conv_id)

    def send_text(self, conv_id: str, text: str) -> str:
        return self._service.process_text(conv_id, text)

    def send_audio(self, conv_id: str, audio_path: str) -> str:
        return self._service.process_audio(conv_id, audio_path)

    def send_file(self, conv_id: str, file_path: str) -> str:
        return self._service.process_file(conv_id, file_path)
