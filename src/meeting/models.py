from dataclasses import dataclass, field

@dataclass
class Meeting:
    id: str
    title: str = ""
    transcript: str = ""
    summary: str = ""
    discussion: str = ""
    decision: str = ""
    suggestions: list[str] = field(default_factory=list)
    next_step: str = ""
    conversation_id: str | None = None
    created_at: str = ""
