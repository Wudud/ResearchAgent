from dataclasses import dataclass, field

@dataclass
class Document:
    id: str
    title: str
    type: str                       # pdf / docx / txt / markdown / python / excel / image
    content: str = ""
    metadata: dict = field(default_factory=dict)
    summary: str = ""
