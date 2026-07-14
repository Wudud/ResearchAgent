import logging
from pathlib import Path

class ExcelExporter:
    def __init__(self):
        self._logger = logging.getLogger("ResearchAgent.ExcelExporter")

    def export(self, sheets: dict[str, list[dict]], output_path: str) -> str:
        try:
            import openpyxl
        except ImportError:
            raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        for sheet_name, rows in sheets.items():
            ws = wb.create_sheet(title=sheet_name[:31])
            if not rows:
                ws.append(["No data"])
                continue

            headers = list(rows[0].keys())
            ws.append(headers)
            for row in rows:
                ws.append([row.get(h, "") for h in headers])

        wb.save(str(path))
        self._logger.info(f"Excel exported to: {path}")
        return str(path)
