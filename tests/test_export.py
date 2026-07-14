import os
from pathlib import Path

import pytest

from src.export.latex_exporter import LatexExporter
from src.export.markdown_exporter import MarkdownExporter
from src.export.csv_exporter import CsvExporter
from src.export.excel_exporter import ExcelExporter
from src.export.plot_exporter import PlotExporter

class TestLatexExporter:
    @pytest.fixture
    def exporter(self):
        return LatexExporter()

    def test_export_experiment_table(self, exporter):
        exps = [
            {"name": "Exp1", "dataset": "DS1", "model": "ResNet", "status": "completed"},
            {"name": "Exp2", "dataset": "DS2", "model": "ViT", "status": "running"},
        ]
        result = exporter.export_experiment_table(exps)
        assert r"\begin{table}" in result
        assert r"\end{table}" in result
        assert "Exp1" in result
        assert "ResNet" in result
        assert "ViT" in result

    def test_export_experiment_table_empty(self, exporter):
        result = exporter.export_experiment_table([])
        assert "No experiments" in result

    def test_export_metrics_table(self, exporter):
        metrics = [
            {"name": "loss", "value": "0.01", "epoch": "1"},
            {"name": "accuracy", "value": "0.98", "epoch": "10"},
        ]
        result = exporter.export_metrics_table(metrics)
        assert r"\begin{table}" in result
        assert "loss" in result
        assert "0.98" in result

    def test_export_dataset_stats(self, exporter):
        stats = {"Total Files": 100, "Size": "1.2 GB"}
        result = exporter.export_dataset_stats(stats)
        assert r"\begin{table}" in result
        assert "Total Files" in result
        assert "1.2 GB" in result

    def test_save(self, exporter, tmp_path):
        path = tmp_path / "test.tex"
        exporter.save(r"\textbf{Hello}", str(path))
        assert path.exists()

    def test_escape_special_chars(self, exporter):
        result = LatexExporter._escape("a & b % c")
        assert "\\&" in result
        assert "\\%" in result

class TestMarkdownExporter:
    @pytest.fixture
    def exporter(self):
        return MarkdownExporter()

    def test_export_experiment_with_front_matter(self, exporter):
        exps = [{"name": "Exp1", "dataset": "DS1", "model": "M1", "status": "done",
                 "metrics": [{"name": "acc", "value": "0.95", "epoch": "10"}]}]
        result = exporter.export_experiment(exps)
        assert "---" in result
        assert "title:" in result
        assert "Exp1" in result
        assert "| acc | 0.95 | 10 |" in result

    def test_export_dataset_stats(self, exporter):
        stats = {"Files": "100", "Size": "1GB"}
        result = exporter.export_dataset_stats(stats)
        assert "---" in result
        assert "| Files | 100 |" in result

    def test_save(self, exporter, tmp_path):
        exporter.save("# Hello", str(path))
        assert path.exists()

class TestCsvExporter:
    @pytest.fixture
    def exporter(self):
        return CsvExporter()

    def test_export_experiments(self, exporter):
        exps = [{"name": "E1", "status": "done"}, {"name": "E2", "status": "running"}]
        result = exporter.export_experiments(exps)
        assert "name" in result
        assert "E1" in result
        assert "E2" in result

    def test_export_experiments_empty(self, exporter):
        result = exporter.export_experiments([])
        assert result == ""

    def test_export_metrics_empty(self, exporter):
        result = exporter.export_metrics([])
        assert result == ""

    def test_save(self, exporter, tmp_path):
        path = tmp_path / "out.csv"
        exporter.save("a,b\n1,2", str(path))
        assert path.exists()

openpyxl = pytest.importorskip("openpyxl", reason="openpyxl not installed")
class TestExcelExporter:
    @pytest.fixture
    def exporter(self):
        from src.export.excel_exporter import ExcelExporter
        return ExcelExporter()

    def test_export(self, exporter, tmp_path):
        path = tmp_path / "out.xlsx"
        sheets = {"Sheet1": [{"A": 1, "B": 2}, {"A": 3, "B": 4}]}
        result = exporter.export(sheets, str(path))
        assert os.path.exists(result)
        assert result.endswith(".xlsx")

mpl = pytest.importorskip("matplotlib", reason="matplotlib not installed")
class TestPlotExporter:
    @pytest.fixture
    def exporter(self):
        return PlotExporter()

    def test_confusion_matrix(self, exporter, tmp_path):
        path = tmp_path / "cm.png"
        cm = [[10, 2], [1, 12]]
        result = exporter.confusion_matrix(cm, ["A", "B"], str(path))
        assert os.path.exists(result)

    def test_loss_curve(self, exporter, tmp_path):
        path = tmp_path / "loss.png"
        result = exporter.loss_curve([0.9, 0.5, 0.1], [0.8, 0.4, 0.2], str(path))
        assert os.path.exists(result)

    def test_loss_curve_no_val(self, exporter, tmp_path):
        path = tmp_path / "loss2.png"
        result = exporter.loss_curve([0.9, 0.5], None, str(path))
        assert os.path.exists(result)

    def test_iou_bar(self, exporter, tmp_path):
        path = tmp_path / "iou.png"
        result = exporter.iou_bar(["cat", "dog"], [0.85, 0.92], str(path))
        assert os.path.exists(result)

    def test_dataset_stats_figure(self, exporter, tmp_path):
        path = tmp_path / "stats.png"
        result = exporter.dataset_stats_figure({".ply": 50, ".pcd": 30}, str(path))
        assert os.path.exists(result)
