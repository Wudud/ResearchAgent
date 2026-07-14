import logging
from datetime import datetime
from pathlib import Path

class MarkdownExporter:
    def __init__(self):
        self._logger = logging.getLogger("ResearchAgent.MarkdownExporter")

    def export_experiment(self, experiments: list[dict], title: str = "Experiment Results") -> str:
        lines = [
            "---",
            f"title: \"{title}\"",
            f"date: \"{datetime.now().strftime('%Y-%m-%d')}\"",
            "---",
            "",
            f"# {title}",
            "",
        ]
        for i, exp in enumerate(experiments, 1):
            lines.append(f"## Experiment {i}: {exp.get('name', 'Unnamed')}")
            lines.append("")
            lines.append(f"- **Dataset**: {exp.get('dataset', 'N/A')}")
            lines.append(f"- **Model**: {exp.get('model', 'N/A')}")
            lines.append(f"- **Status**: {exp.get('status', 'N/A')}")
            if exp.get("parameters"):
                lines.append(f"- **Parameters**: `{exp['parameters']}`")
            if exp.get("metrics"):
                lines.append("")
                lines.append("### Metrics")
                lines.append("")
                lines.append("| Metric | Value | Epoch |")
                lines.append("|--------|-------|-------|")
                for m in exp["metrics"]:
                    lines.append(f"| {m.get('name', '')} | {m.get('value', '')} | {m.get('epoch', '')} |")
            lines.append("")

        return "\n".join(lines)

    def export_dataset_stats(self, stats: dict, title: str = "Dataset Statistics") -> str:
        lines = [
            "---",
            f"title: \"{title}\"",
            f"date: \"{datetime.now().strftime('%Y-%m-%d')}\"",
            "---",
            "",
            f"# {title}",
            "",
            "| Statistic | Value |",
            "|-----------|-------|",
        ]
        for key, value in stats.items():
            lines.append(f"| {key} | {value} |")
        lines.append("")

        return "\n".join(lines)

    def save(self, content: str, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._logger.info(f"Markdown exported to: {path}")
        return str(path)
