import csv
import logging
from pathlib import Path

class CsvExporter:
    def __init__(self):
        self._logger = logging.getLogger("ResearchAgent.CsvExporter")

    def export_experiments(self, experiments: list[dict]) -> str:
        if not experiments:
            self._logger.warning("No experiments to export")
            return ""

        output = self._dicts_to_csv(experiments)
        self._logger.info(f"Exported {len(experiments)} experiments to CSV string")
        return output

    def export_metrics(self, metrics: list[dict]) -> str:
        if not metrics:
            self._logger.warning("No metrics to export")
            return ""

        output = self._dicts_to_csv(metrics)
        self._logger.info(f"Exported {len(metrics)} metrics to CSV string")
        return output

    def save(self, content: str, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8-sig", newline="")
        self._logger.info(f"CSV exported to: {path}")
        return str(path)

    def _dicts_to_csv(self, items: list[dict]) -> str:
        if not items:
            return ""

        keys = []
        seen = set()
        for item in items:
            for k in item:
                if k not in seen:
                    keys.append(k)
                    seen.add(k)

        import io
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(items)
        return buf.getvalue()
