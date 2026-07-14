import logging
from pathlib import Path

class LatexExporter:
    def __init__(self):
        self._logger = logging.getLogger("ResearchAgent.LatexExporter")

    def export_experiment_table(self, experiments: list[dict], caption: str = "Experiment Results", label: str = "tab:experiments") -> str:
        if not experiments:
            return "% No experiments to export"

        cols = self._extract_keys(experiments, ["name", "dataset", "model", "status"])
        header = " & ".join(self._escape(c) for c in cols)
        rows = []
        for exp in experiments:
            vals = [str(exp.get(c, "")) for c in cols]
            rows.append(" & ".join(self._escape(v) for v in vals))

        body = " \\\\\n    ".join(rows)
        return (
            f"\\begin{{table}}[htbp]\n"
            f"  \\centering\n"
            f"  \\caption{{{self._escape(caption)}}}\n"
            f"  \\label{{{label}}}\n"
            f"  \\begin{{tabular}}{{{'l' * len(cols)}}}\n"
            f"    \\hline\n"
            f"    {header} \\\\\n"
            f"    \\hline\n"
            f"    {body} \\\\\n"
            f"    \\hline\n"
            f"  \\end{{tabular}}\n"
            f"\\end{{table}}"
        )

    def export_metrics_table(self, metrics: list[dict], caption: str = "Evaluation Metrics", label: str = "tab:metrics") -> str:
        if not metrics:
            return "% No metrics to export"

        cols = self._extract_keys(metrics, ["name", "value", "epoch"])
        header = " & ".join(self._escape(c) for c in cols)
        rows = []
        for m in metrics:
            vals = [str(m.get(c, "")) for c in cols]
            rows.append(" & ".join(self._escape(v) for v in vals))

        body = " \\\\\n    ".join(rows)
        return (
            f"\\begin{{table}}[htbp]\n"
            f"  \\centering\n"
            f"  \\caption{{{self._escape(caption)}}}\n"
            f"  \\label{{{label}}}\n"
            f"  \\begin{{tabular}}{{{'l' * len(cols)}}}\n"
            f"    \\hline\n"
            f"    {header} \\\\\n"
            f"    \\hline\n"
            f"    {body} \\\\\n"
            f"    \\hline\n"
            f"  \\end{{tabular}}\n"
            f"\\end{{table}}"
        )

    def export_dataset_stats(self, stats: dict, caption: str = "Dataset Statistics", label: str = "tab:dataset") -> str:
        rows = []
        for key, value in stats.items():
            rows.append(f"    {self._escape(str(key))} & {self._escape(str(value))} \\\\")

        body = "\n".join(rows)
        return (
            f"\\begin{{table}}[htbp]\n"
            f"  \\centering\n"
            f"  \\caption{{{self._escape(caption)}}}\n"
            f"  \\label{{{label}}}\n"
            f"  \\begin{{tabular}}{{ll}}\n"
            f"    \\hline\n"
            f"    Statistic & Value \\\\\n"
            f"    \\hline\n"
            f"{body}\n"
            f"    \\hline\n"
            f"  \\end{{tabular}}\n"
            f"\\end{{table}}"
        )

    def save(self, content: str, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._logger.info(f"LaTeX exported to: {path}")
        return str(path)

    def _extract_keys(self, items: list[dict], defaults: list[str]) -> list[str]:
        keys = set()
        for item in items:
            keys.update(item.keys())
        ordered = [k for k in defaults if k in keys]
        remaining = sorted(keys - set(defaults))
        return ordered + remaining

    @staticmethod
    def _escape(text: str) -> str:
        return str(text).replace("\\", "\\textbackslash ").replace("&", "\\&").replace("%", "\\%").replace("$", "\\$").replace("#", "\\#").replace("_", "\\_").replace("{", "\\{").replace("}", "\\}").replace("~", "\\textasciitilde ").replace("^", "\\textasciicircum ")
