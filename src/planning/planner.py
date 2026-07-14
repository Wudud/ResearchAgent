import json
import logging
from datetime import datetime, timezone

from src.planning.models import ResearchPlan
from src.utils.exceptions import PlanningError

class ResearchPlanner:
    """Generate experiment plans from a research direction."""

    def __init__(self, agent):
        self._llm = agent.llm_service
        self._knowledge = agent.knowledge_service if hasattr(agent, 'knowledge_service') else None
        self._logger = logging.getLogger("ResearchAgent.ResearchPlanner")

    def plan(self, research_direction: str) -> ResearchPlan:
        if self._llm is None:
            return self._plan_simple(research_direction)

        # Gather knowledge context for grounding
        context = ""
        if self._knowledge and self._knowledge.available:
            try:
                result = self._knowledge.search(research_direction, top_k=3)
                context = result.get("context", "")
            except Exception as e:
                self._logger.warning(f"Knowledge retrieval failed: {e}")

        try:
            response = self._llm.chat([{"role": "user", "content": prompt}])
            data = self._parse_json(response)
            return ResearchPlan(
                direction=research_direction,
                experiment_name=data.get("experiment_name", ""),
                description=data.get("description", ""),
                dataset=data.get("dataset", ""),
                model=data.get("model", ""),
                parameters=data.get("parameters", {}),
                metrics_to_track=data.get("metrics_to_track", []),
                rationale=data.get("rationale", ""),
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        except (json.JSONDecodeError, ValueError) as e:
            raise PlanningError(f"Failed to parse LLM plan response: {e}") from e
        except Exception as e:
            raise PlanningError(f"Planning failed: {e}") from e

    def _plan_simple(self, direction: str) -> ResearchPlan:
        """Fallback when LLM is unavailable."""
        return ResearchPlan(
            direction=direction,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:] if len(lines) > 1 else lines
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)

class TaskPlanner:
    """Convert an experiment plan into concrete TODO tasks and create them via TaskManager."""

    def __init__(self, task_manager):
        self._task_mgr = task_manager
        self._logger = logging.getLogger("ResearchAgent.TaskPlanner")

    def create_tasks_from_plan(self, plan: ResearchPlan) -> list:
        """Generate TODO tasks from a ResearchPlan and create them."""
        tasks = []

        # Core experiment tasks

        params_str = ", ".join(f"{k}={v}" for k, v in plan.parameters.items())
        if params_str:
            tasks.append({"content": f"Configure parameters: {params_str}", "priority": "high"})

        for metric in plan.metrics_to_track:
            tasks.append({"content": f"Track metric: {metric}", "priority": "medium"})

        # Create in task manager
        created = self._task_mgr.create_tasks_batch(tasks, source="Experiment")
        self._logger.info(f"Created {len(created)} tasks from research plan")
        return created
