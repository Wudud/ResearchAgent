from dataclasses import dataclass, field

from src.assistant.message import Message

@dataclass
class Conversation:
    id: str
    created_at: str = ""
    updated_at: str = ""
    messages: list[Message] = field(default_factory=list)
