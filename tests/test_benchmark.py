from unittest.mock import MagicMock

import pytest

from src.benchmark.runner import BenchmarkRunner

class TestBenchmarkRunner:
    @pytest.fixture
    def runner_no_agent(self):
        return BenchmarkRunner(agent=None)

    def test_run_without_agent_returns_negative(self, runner_no_agent):
        results = runner_no_agent.run()
        assert "embedding_latency_ms" in results
        assert results["embedding_latency_ms"] == -1.0
        assert results["llm_latency_ms"] == -1.0
        assert results["retrieval_latency_ms"] == -1.0
        assert "ram_mb" in results
        assert "gpu" in results
        assert "timestamp" in results

    def test_report_format(self, runner_no_agent):
        report = runner_no_agent.report()
        assert "# ResearchAgent Benchmark Report" in report
        assert "| Embedding Latency" in report
        assert "| GPU " in report

    def test_run_with_mock_agent(self, runner_no_agent):
        agent = MagicMock()
        agent.embedding_service = None
        agent.llm_service = None
        agent.knowledge_service = None
        runner = BenchmarkRunner(agent)
        results = runner.run()
        assert results["embedding_latency_ms"] == -1.0

    def test_bench_ram_returns_value(self, runner_no_agent):
        ram = runner_no_agent._bench_ram()
        assert isinstance(ram, float)

    def test_bench_gpu_returns_dict(self, runner_no_agent):
        gpu = runner_no_agent._bench_gpu()
        assert isinstance(gpu, dict)
        assert "available" in gpu

    def test_report_with_gpu_available(self, runner_no_agent):
        results = runner_no_agent.run()
        results["gpu"] = {"available": True, "name": "Test GPU", "memory_mb": 1024.0}
        report = runner_no_agent.report(results)
        assert "Test GPU" in report
        assert "1024.0" in report
