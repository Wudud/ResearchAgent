from dataclasses import dataclass, field

@dataclass
class ResearchPlan:
    direction: str = ""            # Research direction / goal
    experiment_name: str = ""      # Suggested experiment name
    description: str = ""          # Experiment description
    dataset: str = ""              # Recommended dataset
    model: str = ""                # Recommended model
    parameters: dict = field(default_factory=dict)  # Suggested hyperparameters
    metrics_to_track: list[str] = field(default_factory=list)  # Metrics to monitor
    tasks: list[dict] = field(default_factory=list)  # TODO tasks: {content, priority}
    rationale: str = ""            # Why these choices
    created_at: str = ""
