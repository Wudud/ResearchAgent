from dataclasses import dataclass, field

@dataclass
class Message:
    id: str | None = None
    role: str = "user"              # user / assistant / system
    content: str = ""
    timestamp: str = ""
    message_type: str = "text"      # text / audio / file / system
    attachments: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
