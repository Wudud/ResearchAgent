
import json
from src.mcp.registry import ToolRegistry

def register_all(registry: ToolRegistry):
    """注册所有MCP工具。

    Args:
        registry: ToolRegistry实例
    """
    _register_paper_tools(registry)
    _register_meeting_tools(registry)
    _register_experiment_tools(registry)
    _register_task_tools(registry)
    _register_knowledge_tools(registry)
    _register_dataset_tools(registry)
    _register_memory_tools(registry)
    _register_assistant_tools(registry)

# --- Helpers ---

def _run_dedup(args: dict) -> dict:
    from src.dataset.dedup import PointCloudDedupChecker
    checker = PointCloudDedupChecker(
        voxel_size=args.get("voxel_size", 0.05),
        chamfer_threshold=args.get("chamfer_threshold", 0.01),
    )
    return checker.check_directory(args["root_path"])

def _serialize(obj):
    """JSON-serialize dataclass objects safely using their __dict__."""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: _serialize(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    return str(obj)

# --- Paper Tools ---

def _register_paper_tools(r: ToolRegistry):
    r.register(
        "paper_process",
        "Process and analyze a paper file (PDF, DOCX, etc.)",
        {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]},
        lambda agent, args: _serialize(agent.managers["paper"].process_paper(args["file_path"])),
    )
    r.register(
        "paper_list",
        "List all processed papers",
        {"type": "object", "properties": {}},
        lambda agent, args: _serialize(agent.managers["paper"].list_papers()),
    )
    r.register(
        "paper_search",
        "Search papers by keyword",
        {"type": "object", "properties": {"keyword": {"type": "string"}}, "required": ["keyword"]},
        lambda agent, args: _serialize(agent.managers["paper"].search_paper(args["keyword"])),
    )
    r.register(
        "paper_get",
        "Get a specific paper by ID",
        {"type": "object", "properties": {"paper_id": {"type": "string"}}, "required": ["paper_id"]},
        lambda agent, args: _serialize(agent.managers["paper"].get_paper(args["paper_id"])),
    )

# --- Meeting Tools ---

def _register_meeting_tools(r: ToolRegistry):
    r.register(
        "meeting_process",
        "Process meeting text and extract summary, suggestions, and tasks",
        {"type": "object", "properties": {
            "text": {"type": "string"},
            "title": {"type": "string"},
        }, "required": ["text"]},
        lambda agent, args: _serialize(
            agent.managers["meeting"].process_meeting_text(args["text"], args.get("title"))),
    )
    r.register(
        "meeting_list",
        "List all processed meetings",
        {"type": "object", "properties": {}},
        lambda agent, args: _serialize(agent.managers["meeting"].list_meetings()),
    )
    r.register(
        "meeting_get",
        "Get a specific meeting by ID",
        {"type": "object", "properties": {"meeting_id": {"type": "string"}}, "required": ["meeting_id"]},
        lambda agent, args: _serialize(agent.managers["meeting"].get_meeting(args["meeting_id"])),
    )
    r.register(
        "meeting_weekly_report",
        "Generate a weekly report from all meetings",
        {"type": "object", "properties": {}},
        lambda agent, args: agent.managers["meeting"].generate_weekly_report(),
    )

# --- Experiment Tools ---

def _register_experiment_tools(r: ToolRegistry):
    r.register(
        "experiment_create",
        "Create a new experiment",
        {"type": "object", "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "dataset": {"type": "string"},
            "model": {"type": "string"},
            "parameters": {"type": "object"},
        }, "required": ["name"]},
        lambda agent, args: _serialize(
            agent.managers["experiment"].create_experiment(
                name=args["name"],
                description=args.get("description", ""),
                dataset=args.get("dataset", ""),
                model=args.get("model", ""),
                parameters=args.get("parameters", {}),
            )),
    )
    r.register(
        "experiment_list",
        "List all experiments",
        {"type": "object", "properties": {"status": {"type": "string"}}},
        lambda agent, args: _serialize(agent.managers["experiment"].list_experiments(args.get("status"))),
    )
    r.register(
        "experiment_get",
        "Get a specific experiment by ID",
        {"type": "object", "properties": {"exp_id": {"type": "integer"}}, "required": ["exp_id"]},
        lambda agent, args: _serialize(agent.managers["experiment"].get_experiment(args["exp_id"])),
    )
    r.register(
        "experiment_compare",
        "Compare multiple experiments",
        {"type": "object", "properties": {"exp_ids": {"type": "array", "items": {"type": "integer"}}}, "required": ["exp_ids"]},
        lambda agent, args: agent.managers["experiment"].compare_experiments(args["exp_ids"]),
    )
    r.register(
        "experiment_report",
        "Generate an experiment report",
        {"type": "object", "properties": {"exp_id": {"type": "integer"}}, "required": ["exp_id"]},
        lambda agent, args: agent.managers["experiment"].generate_report(args["exp_id"]),
    )
    r.register(
        "experiment_log_metric",
        "Record a training metric for an experiment",
        {"type": "object", "properties": {
            "exp_id": {"type": "integer"},
            "step": {"type": "integer"},
            "loss": {"type": "number"},
            "mae": {"type": "number"},
            "accuracy": {"type": "number"},
        }, "required": ["exp_id"]},
        lambda agent, args: _serialize(
            agent.managers["experiment"].log_metrics(
                args["exp_id"],
                step=args.get("step"),
                loss=args.get("loss"),
                mae=args.get("mae"),
                accuracy=args.get("accuracy"),
            ) or "ok"),
    )

# --- Task Tools ---

def _register_task_tools(r: ToolRegistry):
    r.register(
        "task_create",
        "Create a new task",
        {"type": "object", "properties": {
            "content": {"type": "string"},
            "source": {"type": "string"},
        }, "required": ["content"]},
        lambda agent, args: _serialize(
            agent.managers["task"].create_task(
                content=args["content"],
                source=args.get("source", ""),
            )),
    )
    r.register(
        "task_list",
        "List tasks with optional filters",
        {"type": "object", "properties": {"status": {"type": "string"}, "source": {"type": "string"}}},
        lambda agent, args: _serialize(
            agent.managers["task"].list_tasks(status=args.get("status"), source=args.get("source"))),
    )
    r.register(
        "task_stats",
        "Get task statistics",
        {"type": "object", "properties": {}},
        lambda agent, args: _serialize(agent.managers["task"].get_stats()),
    )
    r.register(
        "task_update",
        "Update task status",
        {"type": "object", "properties": {
            "task_id": {"type": "integer"},
        }, "required": ["task_id", "status"]},
        lambda agent, args: agent.managers["task"].update_task(
            args["task_id"], status=args.get("status", "")) or "ok",
    )

# --- Knowledge Tools ---

def _register_knowledge_tools(r: ToolRegistry):
    r.register(
        "knowledge_search",
        "Search the knowledge base semantically",
        {"type": "object", "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer"},
            "source_types": {"type": "array", "items": {"type": "string"}},
        }, "required": ["query"]},
        lambda agent, args: _serialize(
            agent.managers["knowledge"].search(
                query=args["query"],
                top_k=args.get("top_k", 5),
                source_types=args.get("source_types"),
            )),
    )
    r.register(
        "knowledge_index",
        "Index a document into the knowledge base",
        {"type": "object", "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
            "source_type": {"type": "string"},
        }, "required": ["title", "content"]},
        lambda agent, args: _serialize(
            agent.managers["knowledge"].index_document(
                title=args["title"],
                content=args["content"],
                metadata={"source_type": args.get("source_type", "document")},
            )),
    )

# --- Dataset Tools ---

def _register_dataset_tools(r: ToolRegistry):
    r.register(
        "dataset_scan",
        "Scan a dataset directory and return file inventory",
        {"type": "object", "properties": {"root_path": {"type": "string"}}},
        lambda agent, args: _serialize(
            agent.managers["dataset"].scan_dataset(args.get("root_path"))),
    )
    r.register(
        "dataset_stats",
        "Generate dataset statistics",
        {"type": "object", "properties": {}},
        lambda agent, args: _serialize(agent.managers["dataset"].get_statistics()),
    )
    r.register(
        "dataset_report",
        "Generate a dataset quality report",
        {"type": "object", "properties": {"dataset_name": {"type": "string"}}},
        lambda agent, args: agent.managers["dataset"].generate_report(args.get("dataset_name", "Dataset")),
    )
    r.register(
        "dataset_dedup_check",
        "Detect duplicate point clouds in a dataset directory (MD5 + Chamfer Distance)",
        {"type": "object", "properties": {
            "root_path": {"type": "string"},
            "voxel_size": {"type": "number"},
            "chamfer_threshold": {"type": "number"},
        }, "required": ["root_path"]},
        lambda agent, args: _serialize(_run_dedup(args)),
    )

# --- Memory Tools ---

def _register_memory_tools(r: ToolRegistry):
    r.register(
        "research_memory_query",
        "Query the research memory (semantic + SQLite fused search)",
        {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        lambda agent, args: _serialize(
            agent.services["research_memory"].search(args["query"])),
    )
    r.register(
        "research_memory_save",
        "Save an item to research memory",
        {"type": "object", "properties": {
            "category": {"type": "string"},
            "title": {"type": "string"},
            "content": {"type": "string"},
            "source": {"type": "string"},
        }, "required": ["category", "title", "content"]},
        lambda agent, args: _serialize(
            agent.services["research_memory"].save_memory(
                category=args["category"],
                title=args["title"],
                content=args["content"],
                source=args.get("source", ""),
            )),
    )

# --- Assistant Tools ---

def _register_assistant_tools(r: ToolRegistry):
    r.register(
        "assistant_chat",
        "Chat with the AI assistant (RAG-enabled)",
        {"type": "object", "properties": {
            "message": {"type": "string"},
            "conversation_id": {"type": "string"},
        }, "required": ["message"]},
        lambda agent, args: agent.managers["assistant"].send_text(
            conv_id=args.get("conversation_id") or agent.managers["assistant"].create_conversation(),
            text=args["message"],
        ),
    )
