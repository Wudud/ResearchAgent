"""
反思Agent模块 - 实现Agent自我反思和输出质量评估。

通过多轮LLM调用对Agent输出进行批判性检查和改进，
将反思结果存储到研究记忆中供未来参考。
"""

import json
import logging


class ReflectionManager:
    """反思管理器 - 对Agent执行结果进行反思评估。

    通过LLM分析执行步骤和结果，生成包含评分、关键洞察、
    错误和改进建议的结构化反思报告，并持久化到研究记忆。

    Attributes:
        _llm: LLM服务实例
        _memory: 研究记忆服务
    """

    def __init__(self, llm_service, memory_service):
        """初始化反思管理器。

        Args:
            llm_service: LLM服务实例
            memory_service: 研究记忆服务实例
        """
        self._llm = llm_service
        self._memory = memory_service
        self._logger = logging.getLogger("ResearchAgent.ReflectionManager")

    def generate_reflection(self, goal: str, steps: list, summary: str) -> dict | None:
        """生成对任务执行的反思评估。

        Args:
            goal: 原始任务目标
            steps: 执行步骤列表
            summary: 任务总结

        Returns:
            dict: 反思结果，包含score、key_insight等字段；LLM不可用时返回None
        """
        if self._llm is None:
            self._logger.warning("LLM not available, skipping reflection")
            return None

        prompt = self._build_prompt(goal, steps, summary)

        try:
            response = self._llm.chat([
                {"role": "system", "content": "你是一位严谨的科研助手。请对刚完成的任务进行反思，输出严格的JSON格式。"},
                {"role": "user", "content": prompt},
            ])
            reflection = self._parse(response)
        except Exception as e:
            self._logger.warning(f"Reflection generation failed: {e}")
            return None

        if reflection is None:
            return None

        # 保存反思到研究记忆
        content = json.dumps(reflection, ensure_ascii=False, indent=2)
        title = reflection.get("key_insight", "Reflection")[:80]
        try:
            self._memory.save_memory(
                category="reflection",
                title=title,
                content=content,
                source=f"goal: {goal[:60]}",
            )
            self._logger.info(f"Reflection saved: {title}")
        except Exception as e:
            self._logger.warning(f"Failed to save reflection to memory: {e}")

        return reflection

    def load_reflections(self, goal: str, top_k: int = 3) -> list[dict]:
        """加载与目标相关的历史反思记录。

        Args:
            goal: 当前任务目标
            top_k: 最多返回的反思数量

        Returns:
            list[dict]: 相关的反思记录列表
        """
        results = self._memory.search(goal)
        reflections = []
        for mem in results:
            if mem.category != "reflection":
                continue
            try:
                reflections.append(json.loads(mem.content))
            except json.JSONDecodeError:
                continue
            if len(reflections) >= top_k:
                break
        return reflections

    def _build_prompt(self, goal: str, steps: list, summary: str) -> str:
        """构建反思提示词。

        Args:
            goal: 原始任务目标
            steps: 执行步骤列表
            summary: 任务总结

        Returns:
            str: 格式化的反思提示词
        """
        steps_text = "\n".join(
            f"{s.get('iteration', '?')}. [{s.get('type', '?')}] {s.get('tool', '')} -> {str(s.get('result', ''))[:200]}"
            for s in steps
        ) if steps else "无步骤记录"

        return f"""请对以下已完成的任务进行反思。

## 原始目标
{goal}

## 执行步骤
{steps_text}

## 任务总结
{summary}

## 输出格式
请以严格的JSON格式输出，不要包含其他文字：
{{
  "type": "reflection",
  "score": <1-5的整数>,
  "key_insight": "本次最核心的发现或洞察",
  "mistake": "本次犯的错误或不足之处（无则填"无"）",
  "improvement": "下次如何改进（无则填"无"）",
  "knowledge_gained": "可复用的经验或知识点"
}}"""

    def _parse(self, raw: str) -> dict | None:
        """解析LLM返回的反思JSON。

        Args:
            raw: LLM原始响应文本

        Returns:
            dict: 解析后的反思数据，解析失败时返回None
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
            if data.get("type") == "reflection":
                return data
            return None
        except json.JSONDecodeError:
            return None
