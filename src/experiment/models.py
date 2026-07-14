from dataclasses import dataclass, field

@dataclass
class Experiment:
    id: int | None = None
    name: str = ""
    status: str = "created"
    description: str = ""
    dataset: str = ""
    model: str = ""
    parameters: dict = field(default_factory=dict)
    metrics: list[dict] = field(default_factory=list)
    log_path: str = ""
    checkpoint_path: str = ""
    tensorboard_path: str = ""
    notes: str = ""
    created_at: str = ""
    completed_at: str = ""
