"""BaseAgent — 领域专用Agent的ReAct循环包装器。

每个领域Agent（论文、会议、实验、数据集）继承此类，
只需重写_register_tools()将其管理器方法暴露为工具即可。
推理逻辑（LLM调用、提示词组装、循环控制）委托给ReasoningService，
使Agent代码保持精简。
"""
import logging

from src.utils.exceptions import AgentError


class BaseAgent:
    """Agent基类 - 实现ReAct（推理-行动）循环的通用框架。

    子类只需注册工具即可，实际的推理和行动循环由ReasoningService处理。
    每个领域Agent（Paper、Meeting、Experiment、Dataset）继承此类。

    Attributes:
        name: Agent名称
        _manager: 关联的业务管理器
        _reasoning: 推理服务实例
        _persona: 角色提示词，定义Agent的行为风格
        _tools: 注册的工具字典 {名称: {描述, 处理器}}
    """

    def __init__(self, name: str, manager, reasoning_service, persona_prompt: str = ""):
        """初始化Agent。

        Args:
            name: Agent名称标识
            manager: 业务管理器实例
            reasoning_service: 推理服务
            persona_prompt: 角色设定提示词
        """
        self.name = name
        self._manager = manager
        self._reasoning = reasoning_service
        self._persona = persona_prompt
        self._tools: dict[str, dict] = {}  # {名称: {描述, 处理函数}}
        self._logger = logging.getLogger(f"ResearchAgent.{name}")

        self._register_tools()

    def _register_tools(self):
        """注册工具 - 子类重写此方法，通过_add_tool()注册工具。"""
        raise NotImplementedError

    def _add_tool(self, name: str, description: str, handler):
        """注册单个工具。

        Args:
            name: 工具名称
            description: 工具功能描述（会提供给LLM）
            handler: 工具执行函数
        """
        self._tools[name] = {"description": description, "handler": handler}

    def _build_tools_description(self) -> str:
        """构建所有已注册工具的描述文本，供LLM理解可用工具。

        Returns:
            str: Markdown格式的工具列表描述
        """
        lines = []
        for name, info in self._tools.items():
            lines.append(f"- **{name}**: {info['description']}")
        return "\n".join(lines)

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """执行指定的工具。

        Args:
            tool_name: 要执行的工具名称
            arguments: 传递给工具的参数

        Returns:
            str: 工具执行结果的字符串表示

        Raises:
            AgentError: 工具未找到或执行失败时抛出
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            return f"未知工具: {tool_name}。可用工具: {list(self._tools.keys())}"
        try:
            result = tool["handler"](**arguments)
            return str(result)
        except Exception as e:
            raise AgentError(f"Tool '{tool_name}' failed: {e}") from e

    def run(self, goal: str) -> dict:
        """执行ReAct循环来完成指定的目标。

        Args:
            goal: 要完成的目标描述

        Returns:
            dict: 包含状态、摘要和步骤的执行结果
                {"status": "completed"|"error", "summary": "...", "steps": [...]}
        """
        return self._reasoning.run_react(
            goal=goal,
            persona_prompt=self._persona,
            tools_desc=self._build_tools_description(),
            tool_executor=self._execute_tool,
        )
