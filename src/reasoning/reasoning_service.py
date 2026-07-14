"""
推理服务模块 - 基于ReAct范式的推理引擎。

实现多轮思考-行动-观察循环，驱动Agent的自主决策。
所有Agent通过此服务进行LLM推理，而非直接调用LLM。
"""

import json
import logging

from src.utils.exceptions import AgentError


class ReasoningService:
    """推理服务 - 统一的LLM推理层。

    职责包括：
    - 提示词组装（角色+工具描述+对话历史）
    - ReAct步骤生成（思考→行动→观察循环）
    - 工具调用JSON的解析和验证

    Attributes:
        _llm: LLM服务
        _prompts: 提示词服务
        _max_iterations: ReAct循环最大迭代次数
        _timeout: 单次操作超时（秒）
    """

    def __init__(self, llm_service, prompt_service=None, max_iterations: int = 5, timeout: int = 300):
        """初始化推理服务。

        Args:
            llm_service: LLM服务实例
            prompt_service: 提示词服务（可选）
            max_iterations: ReAct循环最大迭代次数
            timeout: 超时时间（秒）
        """
        self._llm = llm_service
        self._prompts = prompt_service
        self._max_iterations = max_iterations
        self._timeout = timeout
        self._logger = logging.getLogger("ResearchAgent.ReasoningService")

    @property
    def available(self) -> bool:
        """检查推理服务是否可用。

        Returns:
            bool: LLM服务存在时返回True
        """
        return self._llm is not None

    def run_react(self, goal: str, persona_prompt: str, tools_desc: str, tool_executor) -> dict:
        """运行ReAct循环来完成指定的目标。

        Args:
            goal: 用户的目标描述
            persona_prompt: 领域专用角色提示词
            tools_desc: 可用工具的多行描述
            tool_executor: 工具执行函数，签名为 (tool_name, arguments) -> result_text

        Returns:
            dict: {"status": "completed"|"error", "summary": "...", "steps": [...]}
        """
        if not self.available:
            return {"status": "error", "summary": "LLM not available", "steps": []}

        system_prompt = self._build_system_prompt(persona_prompt, tools_desc)
        history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{goal}\n\n请开始分析并选择合适的工具执行。"},
        ]
        steps = []

        for i in range(self._max_iterations):
            self._logger.info(f"ReAct iteration {i+1}/{self._max_iterations}")
            try:
                response = self._llm.chat(history)
            except Exception as e:
                raise AgentError(f"LLM call failed at iteration {i+1}: {e}") from e

            parsed = self._parse_react_response(response)
            history.append({"role": "assistant", "content": response})

            if parsed["type"] == "finish":
                steps.append({"iteration": i+1, "type": "finish", "summary": parsed["summary"]})
                return {"status": "completed", "summary": parsed["summary"], "steps": steps}

            # 执行工具调用
            tool_name = parsed.get("tool", "")
            tool_args = parsed.get("args", {})
            try:
                result = tool_executor(tool_name, tool_args)
            except Exception as e:
                result = f"Error executing tool '{tool_name}': {e}"

            observation = f"## Result: {tool_name}\n```\n{result}\n```"
            history.append({"role": "user", "content": observation})
            steps.append({"iteration": i+1, "type": "action", "tool": tool_name,
                         "args": tool_args, "result": str(result)[:500]})

        # 达到最大迭代次数，要求LLM总结
        try:
            history.append({"role": "user", "content": "Reached max iterations. Please provide a final summary based on completed actions."})
            final = self._llm.chat(history)
            return {"status": "completed", "summary": final, "steps": steps}
        except Exception:
            return {"status": "completed", "summary": "Reached max iterations without final answer.", "steps": steps}

    def _build_system_prompt(self, persona: str, tools_desc: str) -> str:
        """构建包含角色、工具和回复格式的系统提示词。

        Args:
            persona: 角色设定提示词
            tools_desc: 工具描述文本

        Returns:
            str: 完整的系统提示词
        """
        return f"""{persona}

## Available Tools

{tools_desc}

## Response Format

You must respond in strict JSON format without additional text:

To execute a tool:
{{"type": "action", "tool": "tool_name", "args": {{"param": "value"}}}}

To give final answer:
{{"type": "finish", "summary": "your complete summary"}}

Execute one tool at a time. Give the final summary after completing all necessary operations.
"""

    def _parse_react_response(self, raw: str) -> dict:
        """解析LLM的ReAct响应。

        处理Markdown代码块包裹的JSON，以及直接返回文本的情况。

        Args:
            raw: LLM原始响应文本

        Returns:
            dict: 解析后的响应，格式为 {"type": "action"|"finish", ...}
        """
        text = raw.strip()
        # 去除可能的Markdown代码块包裹
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:] if len(lines) > 1 else lines
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        try:
            data = json.loads(text)
            if "type" not in data:
                return {"type": "finish", "summary": raw}
            return data
        except json.JSONDecodeError:
            # LLM未返回JSON，视为最终答案
            return {"type": "finish", "summary": raw}
