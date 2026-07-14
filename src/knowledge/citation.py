"""
引用管理模块 - 提取和管理文献引用信息。

支持BibTeX解析、引用格式转换和文献去重。
"""


class Citation:
    """引用格式化器 - 将检索结果格式化为可读的引用文本。"""

    def format(self, result: dict) -> str:
        """格式化单条检索结果为引用行。

        Args:
            result: 检索结果字典

        Returns:
            str: 格式化后的引用文本
        """
        meta = result.get("metadata", {})
        source_type = meta.get("source_type", result.get("collection", ""))
        source_label = self._source_label(source_type)
        title = meta.get("title", result.get("id", "Untitled"))
        return f"[{source_label}] {title}"

    def format_batch(self, results: list[dict]) -> str:
        """格式化多条检索结果为引用块。

        Args:
            results: 检索结果列表

        Returns:
            str: 格式化后的引用文本块
        """
        if not results:
            return ""

        grouped: dict[str, list[dict]] = {}
        for r in results:
            source_type = r.get("metadata", {}).get("source_type", r.get("collection", "unknown"))
            grouped.setdefault(source_type, []).append(r)

        lines = []
        for source_type, items in grouped.items():
            label = self._source_label(source_type)
            titles = [item.get("metadata", {}).get("title", item.get("id", "")) for item in items]
            deduped = list(dict.fromkeys(titles))
            lines.append(f"- {label}: " + "; ".join(deduped))

        return "\n".join(lines)

    def inline_citations(self, results: list[dict]) -> str:
        """生成内联引用。

        Args:
            results: 检索结果列表

        Returns:
            str: 内联引用文本
        """
        if not results:
            return ""
        parts = []
        for r in results:
            meta = r.get("metadata", {})
            title = meta.get("title", "")
            if title:
                parts.append(f"[{title}]")
        return " ".join(parts)

    def _source_label(self, source_type: str) -> str:
        """获取来源类型的中文标签。

        Args:
            source_type: 来源类型标识

        Returns:
            str: 中文标签
        """
        labels = {
            "paper": "论文",
            "meeting": "会议",
            "experiment": "实验",
            "dataset": "数据集",
            "methodology": "方法论",
            "knowledge": "知识库",
        }
        return labels.get(source_type, source_type)
