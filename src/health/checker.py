import time
import logging

logger = logging.getLogger("ResearchAgent.HealthChecker")

class HealthChecker:
    """健康检查器 - 检测系统各组件的运行状态。

    """

    def __init__(self, agent):
        self._agent = agent
        self._logger = logging.getLogger("ResearchAgent.HealthChecker")

    def check_all(self) -> dict:
        checks = {
            "llm": self._check_llm(),
            "embedding": self._check_embedding(),
            "sqlite": self._check_sqlite(),
            "chromadb": self._check_chromadb(),
            "config": self._check_config(),
            "workspace": self._check_workspace(),
            "performance": self._check_performance(),
        }

        statuses = [c["status"] for c in checks.values()]
        if "error" in statuses:
            overall = "unhealthy"
        elif "warning" in statuses:
            overall = "degraded"
        else:
            overall = "healthy"

        return {"status": overall, "checks": checks}

    def _check_llm(self) -> dict:
        try:
            if self._agent.llm_service is None:
                return {"status": "warning", "message": "LLM not configured"}
            # Minimal connectivity test — no real AI call
            provider = self._agent.llm_service.provider
            return {"status": "ok", "message": f"LLM configured: {provider}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_embedding(self) -> dict:
        try:
            if self._agent.embedding_service is None or not self._agent.embedding_service.available:
                return {"status": "warning", "message": "Embedding not configured"}
            dim = self._agent.embedding_service.dimension
            return {"status": "ok", "message": f"Embedding available, dim={dim}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_sqlite(self) -> dict:
        try:
            # Lightweight connectivity check — no table creation
            import sqlite3
            db_path = self._agent.config.get("chat.db_path", "./workspace/chat_history.db")
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT 1")
            conn.close()
            return {"status": "ok", "message": f"SQLite connected: {db_path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_chromadb(self) -> dict:
        try:
            import chromadb
            persist_dir = self._agent.config.get("knowledge.persist_dir", "./workspace/chroma_db")
            client = chromadb.PersistentClient(path=persist_dir)
            cols = client.list_collections()
            return {"status": "ok", "message": f"ChromaDB OK, {len(cols)} collections"}
        except Exception as e:
            return {"status": "warning", "message": str(e)}

    def _check_config(self) -> dict:
        # Config validation produces warnings for missing optional config,
        # but only errors for truly broken state (e.g., missing required keys).
        warnings = []
        try:
            warnings = self._agent.config.validate()
        except Exception as e:
            return {"status": "error", "message": str(e)}
        if warnings:
            return {"status": "warning", "message": "; ".join(warnings)}
        return {"status": "ok", "message": "Config valid"}

    def _check_workspace(self) -> dict:
        from pathlib import Path
        ws = self._agent.config.get("agent.workspace_dir", "./workspace")
        p = Path(ws)
        if p.exists():
            return {"status": "ok", "message": f"Workspace exists: {ws}"}
        return {"status": "warning", "message": f"Workspace not found: {ws}"}

    def _check_performance(self) -> dict:
        """Measure RAG retrieval and LLM inference latency for diagnostics."""
        perf = {}

        # RAG retrieval latency — knowledge_service may be None or unavailable
        ks = getattr(self._agent, 'knowledge_service', None)
        if ks is not None and ks.available:
            t0 = time.time()
            try:
                self._agent.knowledge_service.retrieve("health check", top_k=1)
                perf["rag_retrieval_ms"] = round((time.time() - t0) * 1000, 1)
            except Exception:
                perf["rag_retrieval_ms"] = "error"

        # LLM inference latency (lightweight)
        if self._agent.llm_service:
            t0 = time.time()
            try:
                self._agent.llm_service.chat([{"role": "user", "content": "OK"}])
                perf["llm_inference_ms"] = round((time.time() - t0) * 1000, 1)
            except Exception:
                perf["llm_inference_ms"] = "not tested"

        return {"status": "ok", "metrics": perf}
