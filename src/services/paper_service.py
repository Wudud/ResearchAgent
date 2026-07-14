"""
论文服务模块 - 论文分析的核心服务实现。

提供文献管理、引用分析和综述生成功能。
封装论文导入、LLM分析和知识库索引的完整流程。
"""

import json
import json
import logging
from datetime import datetime, timezone

from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService
from src.tools.file_readers.router import FileRouter
from src.persistence.paper_repository import PaperRepository


class PaperService:
    """论文服务 - 论文分析的核心业务逻辑。

    处理论文文件的导入、解析、LLM分析和知识库索引。

    Attributes:
        _llm: LLM服务
        _prompts: 提示词服务
        _repo: 论文仓库
        _router: 文件类型路由器
        _knowledge: 知识库服务（可选）
    """

    def __init__(
        self,
        llm_service: LLMService = None,
        prompt_service: PromptService = None,
        paper_repo: PaperRepository = None,
        knowledge_service=None,
    ):
        self._llm = llm_service
        self._prompts = prompt_service
        self._repo = paper_repo
        self._router = FileRouter()
        self._knowledge = knowledge_service
        self._logger = logging.getLogger("ResearchAgent.PaperService")

    def process_paper(self, file_path: str) -> dict:
        """处理论文文件：读取、分析并保存。

        Args:
            file_path: 论文文件路径

        Returns:
            dict: 处理后的论文数据
        """
        self._logger.info(f"Processing paper: {file_path}")
        doc = self._router.route(file_path)

        full_text = doc.content
        if len(full_text) > 16000:
            full_text = full_text[:16000]

        paper_id = self._repo.create_paper(
            title=doc.title,
            abstract=doc.content[:1000] if doc.content else "",
            file_path=file_path,
        )

        self._analyze(paper_id, full_text)
        paper = self._repo.get(paper_id)
        self._publish("paper.created", {"paper": paper})
        return paper

    def _publish(self, event_type: str, data: dict):
        """发布领域事件。

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        try:
            from src.events.event_bus import EventBus
            EventBus().publish(event_type, data, source="PaperService")
        except Exception:
            pass

    def _analyze(self, paper_id: str, full_text: str = None):
        """使用LLM分析论文内容。

        Args:
            paper_id: 论文ID
            full_text: 论文全文（可选）
        """
        if self._llm is None:
            return

        paper = self._repo.get(paper_id)
        if paper is None:
            return

        text = full_text or getattr(paper, 'abstract', '')
        self._logger.info(f"Analyzing paper: {paper_id}")

        prompt = self._prompts.render("paper/paper_analysis.md", paper_text=text)
        messages = [{"role": "user", "content": prompt}]
        response = self._llm.chat(messages)

        try:
            data = self._parse_json(response)
            updates = {}
            if data.get("title"):
                updates["title"] = data["title"]
            if data.get("authors"):
                updates["authors"] = data["authors"]
            updates["keywords"] = json.dumps(data.get("keywords", []))
            updates["summary"] = data.get("summary", "")
            updates["contributions"] = json.dumps(data.get("contributions", []))
            updates["methodology"] = data.get("methodology", "")
            updates["limitations"] = data.get("limitations", "")
            updates["future_work"] = data.get("future_work", "")
            self._repo.update_paper(paper_id, **updates)
        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(f"Failed to parse paper analysis JSON: {e}")
            self._repo.update_paper(paper_id, summary=response)

    def _parse_json(self, raw: str) -> dict:
        """解析LLM返回的JSON响应。

        Args:
            raw: LLM原始响应

        Returns:
            dict: 解析后的数据
        """
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = lines[1:] if len(lines) > 1 else lines
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines)
        return json.loads(raw)

    def update_memory(self, paper_id: str):
        """将论文更新到知识库中。"""
        if self._knowledge is None or not self._knowledge.available:
            return
        paper = self._repo.get(paper_id)
        if paper is None:
            return
        contributions = getattr(paper, 'contributions', [])
        if isinstance(contributions, str):
            try:
                contributions = json.loads(contributions)
            except json.JSONDecodeError:
                contributions = []
        if contributions:
            title = getattr(paper, 'title', '')
            summary = getattr(paper, 'summary', '')
            text = f"{title}\n{summary}\n{contributions}"
            self._knowledge.index_text("paper", text, {
                "id": str(getattr(paper, 'id', '')),
                "authors": str(getattr(paper, 'authors', '')),
                "keywords": str(getattr(paper, 'keywords', '')),
            })

        methodology = getattr(paper, 'methodology', '')
        if methodology:
            self._knowledge.index_text("methodology", methodology, {
                "id": str(getattr(paper, 'id', '')),
                "title": str(getattr(paper, 'title', '')),
            })

    def get_paper(self, paper_id: str) -> dict | None:
        """获取论文信息。

        Args:
            paper_id: 论文ID

        Returns:
            dict: 论文数据，不存在时返回None
        """
        return self._repo.get(paper_id)

    def list_papers(self, limit: int = 50) -> list[dict]:
        """列出所有论文。

        Args:
            limit: 返回数量限制

        Returns:
            list[dict]: 论文列表
        """
        return self._repo.list_papers(limit)

    def search_paper(self, query: str) -> list:
        """搜索论文。

        Args:
            query: 搜索关键词

        Returns:
            list: 匹配的论文列表
        """
        return self._repo.search(query)

    def search(self, query: str) -> list:
        """搜索论文（别名）。"""
        return self.search_paper(query)

    def process_text_file(self, file_path: str):
        """处理文本文件（别名）。"""
        return self.process_paper(file_path)

    def delete_paper(self, paper_id: str):
        """删除论文。

        Args:
            paper_id: 论文ID
        """
        self._repo.delete_paper(paper_id)
