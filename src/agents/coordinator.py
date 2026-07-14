"""
Agent协调器模块 - 实现多Agent协作的编排逻辑。

负责调度多个领域Agent、管理Agent生命周期，
并可选地启用反思机制对Agent输出进行质量评估。
"""

import logging

from src.reasoning.reasoning_service import ReasoningService
from src.agents.paper import PaperAgent
from src.agents.meeting import MeetingAgent
from src.agents.experiment import ExperimentAgent
from src.agents.dataset import DatasetAgent
from src.agents.reflection import ReflectionManager
from src.utils.exceptions import AgentError


class AgentCoordinator:
    """Agent协调器 - 管理多个领域Agent的创建、调度和协作。

    负责初始化各领域Agent，将任务分发给对应Agent执行，
    并在配置启用时通过ReflectionManager对输出进行反思评估。

    Attributes:
        _agent: 父级ResearchAgent实例
        _agents: 已注册的领域Agent字典
        _reflection: 可选的反思管理器
        _enable_reflection: 是否启用反思机制
    """

    def __init__(self, agent):
        """初始化Agent协调器。

        Args:
            agent: ResearchAgent实例
        """
        self._agent = agent
        self._agents: dict[str, object] = {}
        self._reflection: ReflectionManager | None = None
        self._enable_reflection: bool = False
        self._logger = logging.getLogger("ResearchAgent.AgentCoordinator")
        self._init_agents()

    def _init_agents(self):
        """初始化所有配置的领域Agent。

        根据可用的管理器创建对应的Agent实例，
        如果配置启用了反思机制，则初始化ReflectionManager。
        """
        config = self._agent.config
        max_iter = config.get("agents.react.max_iterations", 5)
        timeout = config.get("agents.react.timeout", 300)
        self._enable_reflection = config.get("agents.react.enable_reflection", False)

        llm = self._agent.llm_service
        prompts = self._agent.services.get("prompt")
        reasoning = ReasoningService(llm, prompts, max_iterations=max_iter, timeout=timeout)

        managers = self._agent.managers

        if "paper" in managers:
            self._agents["paper"] = PaperAgent(managers["paper"], reasoning)
        if "meeting" in managers:
            self._agents["meeting"] = MeetingAgent(managers["meeting"], reasoning)
        if "experiment" in managers:
            self._agents["experiment"] = ExperimentAgent(managers["experiment"], reasoning)
        if "dataset" in managers:
            self._agents["dataset"] = DatasetAgent(managers["dataset"], reasoning)

        if self._enable_reflection:
            memory_svc = self._agent.services.get("research_memory")
            if memory_svc:
                self._reflection = ReflectionManager(llm, memory_svc)
                self._logger.info("Reflection enabled")
            else:
                self._logger.warning("enable_reflection=true but research_memory service not found")

        self._logger.info(f"AgentCoordinator initialized with agents: {list(self._agents.keys())}")

    def run_agent(self, agent_type: str, goal: str) -> dict:
        """将任务分发给指定类型的Agent执行。

        Args:
            agent_type: Agent类型（"paper"、"meeting"、"experiment"或"dataset"）
            goal: 自然语言描述的任务目标

        Returns:
            dict: {"status": "completed"|"error", "summary": "...", "steps": [...]}

        Raises:
            AgentError: 未知的Agent类型时抛出
        """
        ag = self._agents.get(agent_type)
        if ag is None:
            valid = list(self._agents.keys())
            raise AgentError(f"Unknown agent type: '{agent_type}'. Valid types: {valid}")
        result = ag.run(goal)

        # 如果启用了反思，对成功的结果进行反思评估
        if result.get("status") == "completed" and self._reflection:
            try:
                reflection = self._reflection.generate_reflection(
                    goal=goal,
                    steps=result.get("steps", []),
                    summary=result.get("summary", ""),
                )
                if reflection:
                    result["reflection"] = reflection
            except Exception as e:
                self._logger.warning(f"Reflection failed (non-blocking): {e}")

        return result

    @property
    def available_agents(self) -> list[str]:
        """返回当前可用的Agent类型列表。"""
        return list(self._agents.keys())
