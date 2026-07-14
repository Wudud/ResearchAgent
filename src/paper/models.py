from dataclasses import dataclass, field

@dataclass
class Paper:
    id: str
    title: str = ""
    authors: str = ""
    abstract: str = ""
    sections: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    summary: str = ""
    contributions: list[str] = field(default_factory=list)
    methodology: str = ""
    limitations: str = ""
    future_work: str = ""
    reference: str = ""
    file_path: str = ""
    created_at: str = ""
