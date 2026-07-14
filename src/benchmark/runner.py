import logging
import time
from datetime import datetime

class BenchmarkRunner:
    def __init__(self, agent=None):
        self._agent = agent
        self._logger = logging.getLogger("ResearchAgent.Benchmark")

    def run(self) -> dict:
        results = {
            "timestamp": datetime.now().isoformat(),
            "embedding_latency_ms": self._bench_embedding(),
            "llm_latency_ms": self._bench_llm(),
            "retrieval_latency_ms": self._bench_retrieval(),
            "ram_mb": self._bench_ram(),
            "gpu": self._bench_gpu(),
        }
        return results

    def report(self, results: dict = None) -> str:
        if results is None:
            results = self.run()

        lines = [
            "# ResearchAgent Benchmark Report",
            "",
            f"**Date**: {results.get('timestamp', 'N/A')}",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Embedding Latency | {results.get('embedding_latency_ms', 'N/A')} ms |",
            f"| LLM Latency | {results.get('llm_latency_ms', 'N/A')} ms |",
            f"| Retrieval Latency | {results.get('retrieval_latency_ms', 'N/A')} ms |",
            f"| RAM Usage | {results.get('ram_mb', 'N/A')} MB |",
        ]

        gpu = results.get("gpu", {})
        if gpu and gpu.get("available"):
            lines.append(f"| GPU Memory | {gpu.get('memory_mb', 'N/A')} MB |")
            lines.append(f"| GPU Name | {gpu.get('name', 'N/A')} |")
        else:
            lines.append("| GPU | Not available |")

        return "\n".join(lines) + "\n"

    def _bench_embedding(self) -> float:
        if self._agent is None or self._agent.embedding_service is None or not self._agent.embedding_service.available:
            return -1.0
        svc = self._agent.embedding_service
        sample = "Benchmark test sentence for embedding."
        start = time.perf_counter()
        try:
            svc.embed(sample)
            return round((time.perf_counter() - start) * 1000, 2)
        except Exception:
            return -1.0

    def _bench_llm(self) -> float:
        if self._agent is None or self._agent.llm_service is None:
            return -1.0
        svc = self._agent.llm_service
        messages = [{"role": "user", "content": "Say 'ok' and nothing else."}]
        start = time.perf_counter()
        try:
            svc.chat(messages)
            return round((time.perf_counter() - start) * 1000, 2)
        except Exception:
            return -1.0

    def _bench_retrieval(self) -> float:
        if self._agent is None or self._agent.knowledge_service is None or not self._agent.knowledge_service.available:
            return -1.0
        svc = self._agent.knowledge_service
        start = time.perf_counter()
        try:
            svc.retrieve("benchmark test query", top_k=3)
            return round((time.perf_counter() - start) * 1000, 2)
        except Exception:
            return -1.0

    def _bench_ram(self) -> float:
        try:
            import psutil
            proc = psutil.Process()
            return round(proc.memory_info().rss / (1024 * 1024), 2)
        except ImportError:
            return -1.0
        except Exception:
            return -1.0

    def _bench_gpu(self) -> dict:
        result = {"available": False}

        try:
            import torch
            if torch.cuda.is_available():
                result["available"] = True
                result["name"] = torch.cuda.get_device_name(0)
                result["memory_mb"] = round(torch.cuda.memory_allocated(0) / (1024 * 1024), 2)
                result["total_memory_mb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024), 2)
                return result
        except ImportError:
            pass
        except Exception:
            pass

        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            result["available"] = True
            result["name"] = pynvml.nvmlDeviceGetName(handle)
            result["memory_mb"] = round(info.used / (1024 * 1024), 2)
            result["total_memory_mb"] = round(info.total / (1024 * 1024), 2)
            pynvml.nvmlShutdown()
            return result
        except ImportError:
            pass
        except Exception:
            pass

        return result
