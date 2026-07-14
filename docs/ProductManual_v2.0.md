# ResearchAgent v2.0 产品说明书

---

## 目录

1. [产品概述](#1-产品概述)
2. [系统架构](#2-系统架构)
3. [功能清单](#3-功能清单)
4. [接口文档](#4-接口文档)
5. [配置说明](#5-配置说明)
6. [使用指南](#6-使用指南)
7. [扩展开发指南](#7-扩展开发指南)
8. [附录](#8-附录)

---

## 1. 产品概述

### 1.1 产品简介

ResearchAgent 是一个面向科学研究全过程的 AI 智能体平台。以大语言模型（LLM）为核心推理引擎，集成了数据集管理、实验追踪、论文分析、会议纪要、知识库检索、点云数据处理等功能，覆盖从数据准备到论文产出的完整科研流程。

### 1.2 核心能力

| 领域 | 能力 |
|------|------|
| 数据集管理 | 多格式文件扫描、完整性校验、点云统计、重复检测（MD5 + Chamfer Distance） |
| 实验管理 | 实验 CRUD、参数记录、指标追踪、实验对比 |
| 论文分析 | PDF/DOCX 解析、创新点提取、知识库索引 |
| 会议分析 | 语音转文字（ASR）、会议摘要、TODO 提取、周报生成 |
| 知识库 | ChromaDB 向量存储 + Reranker 重排序 + RAG 检索增强 |
| Agent 智能体 | 4 个领域 ReAct Agent（Paper/Meeting/Experiment/Dataset） |
| Reflection | 任务完成后自动反思，经验持久化存储 |
| 论文产出 | LaTeX 表格、学术 Markdown、CSV/Excel、图表（Confusion Matrix/Loss/IoU） |
| Benchmark | Embedding/LLM/Retrieval/RAM/GPU 全链路性能统计 |
| 部署 | Docker 一键部署，支持 CPU/GPU |

### 1.3 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| LLM | OpenAI API / 兼容接口 |
| Embedding | all-MiniLM-L6-v2 (本地) / text-embedding-3-small (云端) |
| ASR | faster-whisper (本地) / OpenAI Whisper (云端) |
| 向量数据库 | ChromaDB |
| 关系数据库 | SQLite |
| Web UI | Streamlit |
| 配置 | YAML + 环境变量 |
| 容器化 | Docker + docker-compose |
| 测试 | pytest (301 用例) |

---

## 2. 系统架构

### 2.1 架构总览

```text
┌──────────────────────────────────────────────────────────────┐
│                     Web UI (Streamlit)                        │
│           8 Pages: Chat / Paper / Meeting / Exp /             │
│                Dataset / Knowledge / Memory / Settings        │
├──────────────────────────────────────────────────────────────┤
│                     CLI (10 subcommands)                      │
│    workflow / web / agent run / mcp-server / health /         │
│    export / dataset dedup / benchmark                         │
├──────────────────────────────────────────────────────────────┤
│                  MCP Server (24 tools)                         │
│          stdio JSON-RPC — Cursor / Claude 集成                │
├──────────────────────────────────────────────────────────────┤
│                   Agent Coordinator                           │
│    ┌──────────┬──────────┬──────────┬──────────┐             │
│    │  Paper   │ Meeting  │Experiment│ Dataset  │             │
│    │  Agent   │  Agent   │  Agent   │  Agent   │             │
│    └──────────┴──────────┴──────────┴──────────┘             │
│              ReflectionManager (自动反思)                     │
├──────────────────────────────────────────────────────────────┤
│                     Reasoning Layer                            │
│    ReAct Loop (Think → Act → Observe → Reflect)               │
├──────────────────────────────────────────────────────────────┤
│                       Services                                 │
│    LLM │ Embedding │ ASR │ Vision │ Knowledge │ Memory         │
│    Prompt │ Report │ ResearchMemory │ Task                    │
├──────────────────────────────────────────────────────────────┤
│                   Knowledge & Memory                           │
│    ChromaDB RAG │ Reranker │ Semantic Memory │ Cache           │
├──────────────────────────────────────────────────────────────┤
│                     Persistence                                │
│    7 Repositories (Conversation/Meeting/Paper/                │
│    Task/ResearchMemory/Experiment/Knowledge)                  │
├──────────────────────────────────────────────────────────────┤
│                 Workflows & Events                             │
│    Paper │ Meeting │ Experiment │ Dataset │ AutoIndex          │
│    EventBus + Listener                                        │
├──────────────────────────────────────────────────────────────┤
│                        Tools                                   │
│    FileScanner │ Checksum │ PLY/PCD Reader │                  │
│    PointCloud Statistics │ Dedup Checker                      │
├──────────────────────────────────────────────────────────────┤
│                      Export Layer                              │
│    LaTeX │ Markdown │ CSV │ Excel │ Plot                       │
├──────────────────────────────────────────────────────────────┤
│                    Infrastructure                              │
│    Config Manager │ Logging │ Exception │ Cache                 │
│    Benchmark │ Docker │ Health Checker                         │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```text
用户输入 (CLI / Web / MCP)
        │
        ▼
  AgentCoordinator
        │
        ├── Workflow 模式 ──→ Workflow Engine ──→ Manager ──→ Tools
        │
        └── Agent 模式 ──→ DomainAgent ──→ ReasoningService (ReAct)
                                    │
                              LLM Chat (with Cache)
                                    │
                              工具调用 → 结果
                                    │
                              完成 → ReflectionManager
                                    │
                              写入 ResearchMemory
```

### 2.3 模块职责

| 层级 | 职责 | 核心文件 |
|------|------|----------|
| **Web** | Streamlit 用户界面 | `src/web/app.py` + 8 pages |
| **CLI** | 命令行入口 | `main.py`, `src/cli/commands.py` |
| **MCP** | stdio JSON-RPC 工具服务 | `src/mcp/server.py`, `tools.py` |
| **Agents** | 领域 Agent + 协调器 + 反思 | `src/agents/` |
| **Reasoning** | ReAct 推理循环 | `src/reasoning/` |
| **Managers** | 7 个业务 Manager | `src/managers/` |
| **Services** | 12 个服务层 | `src/services/` |
| **Knowledge** | RAG 知识库 | `src/knowledge/` |
| **Memory** | 语义记忆 | `src/memory/` |
| **Persistence** | 7 个 Repository | `src/persistence/` |
| **Workflows** | 5 个工作流 | `src/workflows/` |
| **Dataset** | 数据集处理 | `src/dataset/` |
| **Export** | 学术论文导出 | `src/export/` |
| **Tools** | 底层工具 | `src/tools/` |
| **Cache** | 性能缓存 | `src/utils/cache.py` |
| **Benchmark** | 性能基准测试 | `src/benchmark/` |

---

## 3. 功能清单

### 3.1 CLI 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `workflow paper` | 论文处理流水线 | `--file paper.pdf` |
| `workflow meeting` | 会议分析流水线 | `--audio meeting.wav` |
| `workflow experiment` | 实验全生命周期 | `--name exp1 --dataset ds1` |
| `workflow dataset` | 数据集分析流水线 | `--root ./data` |
| `workflow auto-index` | 批量索引知识库 | |
| `web` | 启动 Streamlit Web UI | |
| `agent run` | 运行 ReAct Agent | `--type experiment --goal "..."` |
| `mcp-server` | 启动 MCP stdio 服务器 | |
| `health` | 系统健康检查 | |
| `export` | 论文材料导出 | `--type experiment --format latex` |
| `dataset dedup` | 点云重复检测 | `--root ./data --voxel-size 0.05` |
| `benchmark` | 性能基准测试 | |

### 3.2 Web UI 页面（8 页）

| 页面 | 功能 |
|------|------|
| **Chat** | RAG 增强的 AI 对话助手 |
| **Paper** | 论文上传、解析、知识库索引 |
| **Meeting** | 会议文本/音频分析、摘要生成 |
| **Experiment** | 实验创建、参数管理、指标追踪、对比 |
| **Dataset** | 数据集扫描、统计、完整性校验、去重 |
| **Knowledge** | 知识库搜索、文档管理 |
| **Memory** | 研究记忆浏览与搜索 |
| **Settings** | 系统配置管理 |

### 3.3 MCP Tools（24 个）

#### Paper（4 tools）
| Tool | 说明 |
|------|------|
| `paper_process` | 处理论文文件（PDF/DOCX） |
| `paper_list` | 列出所有论文 |
| `paper_search` | 按关键字搜索论文 |
| `paper_get` | 按 ID 获取论文详情 |

#### Meeting（4 tools）
| Tool | 说明 |
|------|------|
| `meeting_process` | 处理会议文本，提取摘要/建议/任务 |
| `meeting_list` | 列出所有会议 |
| `meeting_get` | 按 ID 获取会议详情 |
| `meeting_weekly_report` | 生成周报 |

#### Experiment（6 tools）
| Tool | 说明 |
|------|------|
| `experiment_create` | 创建新实验 |
| `experiment_list` | 列出实验，可按状态筛选 |
| `experiment_get` | 按 ID 获取实验 |
| `experiment_compare` | 多实验对比 |
| `experiment_report` | 生成实验报告 |
| `experiment_log_metric` | 记录训练指标 |

#### Task（4 tools）
| Tool | 说明 |
|------|------|
| `task_create` | 创建任务 |
| `task_list` | 列出任务 |
| `task_stats` | 任务统计 |
| `task_update` | 更新任务状态 |

#### Knowledge（2 tools）
| Tool | 说明 |
|------|------|
| `knowledge_search` | 语义搜索知识库 |
| `knowledge_index` | 索引文档到知识库 |

#### Dataset（4 tools）
| Tool | 说明 |
|------|------|
| `dataset_scan` | 扫描数据集目录 |
| `dataset_stats` | 生成数据集统计 |
| `dataset_report` | 生成数据集质量报告 |
| `dataset_dedup_check` | 点云重复检测（MD5 + Chamfer） |

#### Memory（2 tools）
| Tool | 说明 |
|------|------|
| `research_memory_query` | 融合搜索研究记忆 |
| `research_memory_save` | 保存研究记忆 |

#### Assistant（1 tool）
| Tool | 说明 |
|------|------|
| `assistant_chat` | RAG 增强对话 |

### 3.4 Agent 智能体

| Agent | 领域 | 核心 Manager |
|-------|------|-------------|
| PaperAgent | 论文分析 | PaperManager |
| MeetingAgent | 会议分析 | MeetingManager |
| ExperimentAgent | 实验管理 | ExperimentManager |
| DatasetAgent | 数据集管理 | DatasetManager |

每个 Agent 均执行标准 ReAct 循环（Think → Act → Observe），支持自主工具调用和 Reflection 反思。

### 3.5 Workflow（5 个工作流）

| 工作流 | 流水线 |
|--------|--------|
| PaperWorkflow | 文件解析 → 信息提取 → 知识库索引 |
| MeetingWorkflow | 文本/音频输入 → 摘要 → 建议 → 任务提取 → 索引 |
| ExperimentWorkflow | 创建 → 参数配置 → 指标记录 → 报告 |
| DatasetWorkflow | 扫描 → 统计 → 完整性校验 → 报告 → 去重 |
| AutoIndexWorkflow | 批量索引所有历史数据到知识库 |

### 3.6 学术导出

| 格式 | 支持内容 |
|------|----------|
| **LaTeX** | 实验表格、评估指标表、数据集统计表 |
| **Markdown** | Front Matter + 表格（可直接作为论文附录） |
| **CSV** | 实验记录、指标数据 |
| **Excel** | 多 Sheet 工作簿 |
| **Plot** | Confusion Matrix、Loss Curve、IoU Bar、数据集分布饼图 |

### 3.7 性能优化

| 缓存 | 类型 | 作用域 |
|------|------|--------|
| EmbeddingCache | LRU | text → embedding 向量 |
| LLMResponseCache | TTL | messages → response |
| ChromaCollectionCache | TTL | 集合句柄复用 |

### 3.8 数据去重

| 方法 | 说明 |
|------|------|
| MD5 精确去重 | 文件内容哈希比对 |
| Voxel 降采样 | 点云体素化降维 |
| Chamfer Distance | 基于 scipy cKDTree 的近重复检测 |

---

## 4. 接口文档

### 4.1 ResearchAgent（核心入口）

**文件：** `src/core/agent.py`

```python
class ResearchAgent:
    def __init__(self, config_path: str = None)
    def initialize(self, quiet: bool = False) -> None
```

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `config` | `ConfigManager` | 配置管理器 |
| `logger` | `logging.Logger` | 日志实例 |
| `llm_service` | `LLMService \| None` | LLM 服务 |
| `embedding_service` | `EmbeddingService` | 向量化服务 |
| `asr_service` | `ASRService` | 语音识别服务 |
| `vision_service` | `VisionService` | 视觉服务 |
| `knowledge_service` | `KnowledgeService` | 知识库服务 |
| `services` | `dict` | 全部服务字典（12 个） |
| `tools` | `dict` | 工具字典（5 个） |
| `managers` | `dict` | Manager 字典（7 个） |
| `workflows` | `dict` | Workflow 字典（5 个） |
| `coordinator` | `AgentCoordinator` | Agent 协调器（懒加载） |

### 4.2 ConfigManager

**文件：** `src/config/config_manager.py`

```python
class ConfigManager:
    def __init__(self, config_path: str = None)
    def get(self, key_path: str, default=None) -> Any
    def validate(self) -> list[str]
```

`get()` 支持点号路径：`config.get("llm.providers.openai.model")`
`${ENV_VAR}` 语法自动解析环境变量。

### 4.3 AgentCoordinator

**文件：** `src/agents/coordinator.py`

```python
class AgentCoordinator:
    def run_agent(self, agent_type: str, goal: str) -> dict
    @property
    def available_agents(self) -> list[str]
```

**返回值：**

```json
{
  "status": "completed",
  "summary": "任务总结",
  "steps": [
    {"iteration": 1, "type": "action", "tool": "dataset_scan", "args": {...}, "result": "..."}
  ],
  "reflection": {
    "type": "reflection",
    "score": 4,
    "key_insight": "核心发现",
    "mistake": "不足",
    "improvement": "改进",
    "knowledge_gained": "经验"
  }
}
```

### 4.4 ReflectionManager

**文件：** `src/agents/reflection.py`

```python
class ReflectionManager:
    def __init__(self, llm_service, memory_service)
    def generate_reflection(self, goal: str, steps: list, summary: str) -> dict | None
    def load_reflections(self, goal: str, top_k: int = 3) -> list[dict]
```

### 4.5 ReasoningService

**文件：** `src/reasoning/reasoning_service.py`

```python
class ReasoningService:
    def __init__(self, llm_service, prompt_service=None, max_iterations=5, timeout=300)
    def run_react(self, goal, persona_prompt, tools_desc, tool_executor) -> dict
```

ReAct 循环最多 5 轮，每轮：LLM 推理 → JSON 解析 → 工具调用 → 观察结果。

### 4.6 LLMService

**文件：** `src/services/llm_service.py`

```python
class LLMService:
    def __init__(self, adapter: BaseLLMAdapter, cache=None)
    def chat(self, messages: list[dict], **kwargs) -> str
    def chat_stream(self, messages: list[dict], **kwargs) -> Iterator[str]
    @property
    def provider(self) -> str
    @property
    def total_tokens(self) -> int
```

支持 TTL 响应缓存。

### 4.7 EmbeddingService

**文件：** `src/services/embedding_service.py`

```python
class EmbeddingService:
    def __init__(self, adapter: BaseEmbeddingAdapter = None, cache=None)
    def embed(self, text: str) -> list[float]
    def embed_batch(self, texts: list[str]) -> list[list[float]]
    @property
    def available(self) -> bool
    @property
    def dimension(self) -> int
```

支持 LRU 缓存。

### 4.8 KnowledgeService

**文件：** `src/services/knowledge_service.py`

```python
class KnowledgeService:
    def index_text(self, source_type: str, text: str, metadata: dict = None) -> int
    def retrieve(self, query: str, source_types: list[str] = None, top_k: int = 5) -> list[dict]
    def search(self, query: str, source_types: list[str] = None, top_k: int = 5) -> dict
    def clear_source(self, source_type: str)
    def get_source_count(self, source_type: str) -> int
```

流程：Chunking → Embedding → ChromaDB Index → Query → Reranker → Citation

### 4.9 ResearchMemoryService

**文件：** `src/services/research_memory_service.py`

```python
class ResearchMemoryService:
    def save_memory(self, category, title, content, source="", importance="中") -> ResearchMemory
    def get_memory(self, memory_id: str) -> ResearchMemory | None
    def list_by_category(self, category: str = None) -> list[ResearchMemory]
    def search(self, keyword: str) -> list[ResearchMemory]        # SQLite + Semantic 融合搜索
    def delete_memory(self, memory_id: str)
    def get_relevant_context(self, query: str, max_results=5) -> str
```

### 4.10 Export 导出

**文件：** `src/export/`

```python
class LatexExporter:
    def export_experiment_table(experiments: list[dict], ...) -> str
    def export_metrics_table(metrics: list[dict], ...) -> str
    def export_dataset_stats(stats: dict, ...) -> str
    def save(content: str, output_path: str) -> str

class MarkdownExporter:
    def export_experiment(experiments: list[dict], title: str) -> str
    def export_dataset_stats(stats: dict, title: str) -> str
    def save(content: str, output_path: str) -> str

class CsvExporter:
    def export_experiments(experiments: list[dict]) -> str
    def export_metrics(metrics: list[dict]) -> str
    def save(content: str, output_path: str) -> str

class ExcelExporter:
    def export(sheets: dict[str, list[dict]], output_path: str) -> str

class PlotExporter:
    def confusion_matrix(cm, labels, output_path, title) -> str
    def loss_curve(train_loss, val_loss, output_path, title) -> str
    def iou_bar(categories, iou_values, output_path, title) -> str
    def dataset_stats_figure(extension_counts, output_path, title) -> str
```

### 4.11 PointCloudDedupChecker

**文件：** `src/dataset/dedup.py`

```python
class PointCloudDedupChecker:
    def __init__(self, voxel_size: float = 0.05, chamfer_threshold: float = 0.01)
    def check_directory(self, root: str) -> dict
    def generate_report(self, result: dict, output_path: str = None) -> str
```

返回：`{total_files, unique_files, exact_duplicates, near_duplicate_pairs, md5_groups, near_duplicates}`

### 4.12 BenchmarkRunner

**文件：** `src/benchmark/runner.py`

```python
class BenchmarkRunner:
    def __init__(self, agent=None)
    def run(self) -> dict       # {embedding_latency_ms, llm_latency_ms, retrieval_latency_ms, ram_mb, gpu}
    def report(self, results=None) -> str
```

### 4.13 Cache

**文件：** `src/utils/cache.py`

```python
class EmbeddingCache:           # LRU, thread-safe
    def get(self, text: str) -> list[float] | None
    def set(self, text: str, embedding: list[float])
    @property
    def hit_rate(self) -> float

class LLMResponseCache:         # TTL, thread-safe
    def get(self, messages: list[dict]) -> str | None
    def set(self, messages: list[dict], response: str)
    @property
    def hit_rate(self) -> float

class ChromaCollectionCache:    # TTL
    def get(self, name: str) -> object | None
    def set(self, name: str, collection: object)
    def invalidate(self, name: str)
```

### 4.14 数据模型

**文件：** `src/dataset/models.py`, `src/experiment/models.py`, `src/persistence/`

```python
@dataclass
class DatasetInventory:
    root_path: str; files: list[FileEntry]; total_files: int
    total_size_bytes: int; extension_counts: dict[str, int]

@dataclass
class DatasetStats:
    total_files: int; total_size_human: str; point_cloud_files: int
    ply_files: int; pcd_files: int; avg_point_count: float | None
    min_point_count: int | None; max_point_count: int | None

@dataclass
class Experiment:
    id: int | None; name: str; dataset: str; model: str
    parameters: dict; metrics: list[dict]; status: str; notes: str

@dataclass
class ResearchMemory:
    id: str; category: str; title: str; content: str
    source: str; importance: str; created_at: str
```

### 4.15 异常层级

```text
ResearchAgentError (Exception)
├── ConfigError         — 配置文件错误
├── LLMError            — LLM API 调用错误
├── ToolError           — 工具执行错误
├── AgentError          — Agent 执行错误
└── ManagerError        — Manager 级别错误
```

---

## 5. 配置说明

### 5.1 完整配置选项

**文件：** `configs/default.yaml`

```yaml
agent:
  name: ResearchAgent
  version: "0.2.0"
  workspace_dir: "./workspace"

llm:
  default_provider: openai
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      base_url: https://api.openai.com/v1
      model: gpt-4o
      temperature: 0.3
      max_tokens: 4096

embedding:
  default_provider: local
  providers:
    local:
      model_name: all-MiniLM-L6-v2
      device: cpu
    openai:
      api_key: ${OPENAI_API_KEY}
      model: text-embedding-3-small

asr:
  default_provider: local
  providers:
    local:
      model_size: base
      device: cpu
      compute_type: int8
    openai:
      api_key: ${OPENAI_API_KEY}
      model: whisper-1
      language: zh

vision:
  default_provider: null
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4o

dataset:
  root_dir: "./workspace/datasets"
  allowed_extensions: [.ply, .pcd, .pts, .xyz, .xyzrgb, .npy]

knowledge:
  persist_dir: "./workspace/chroma_db"
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"

chat:
  context_window: 20
  upload_dir: "./workspace/uploads"
  db_path: "./workspace/chat_history.db"

agents:
  react:
    max_iterations: 5
    timeout: 300
    enable_reflection: false

mcp:
  enabled: true
  server_name: ResearchAgent
  protocol_version: "2024-11-05"

web:
  host: localhost
  port: 8501

logging:
  level: INFO
  log_dir: "./logs"
  max_bytes_per_file: 10485760
  backup_count: 3

cache:
  embedding: false          # 启用 Embedding LRU 缓存
  llm: false                # 启用 LLM TTL 响应缓存
  chroma: false             # 启用 ChromaDB 集合缓存

workspace:
  uploads_dir: "./workspace/uploads"
  meetings_dir: "./workspace/meetings"
  papers_dir: "./workspace/papers"
  reports_dir: "./workspace/reports"
```

### 5.2 环境变量

| 变量 | 用途 | 必需 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | LLM/Embedding/Vision/ASR 云端功能 |

---

## 6. 使用指南

### 6.1 环境准备

#### 本地安装

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置 API Key
export OPENAI_API_KEY=sk-your-key   # Linux/Mac
set OPENAI_API_KEY=sk-your-key      # Windows
```

#### Docker 部署

```bash
# 生产环境（CPU）
docker compose up research-agent-cpu

# 开发环境（热更新）
docker compose --profile dev up research-agent-dev

# GPU 环境
docker compose --profile gpu up research-agent

# 健康检查
docker compose run research-agent-cpu python main.py health

# MCP Server
docker compose run research-agent-cpu python main.py mcp-server
```

### 6.2 Web UI 启动

```bash
# 方式一
python run_web.py

# 方式二
streamlit run src/web/app.py

# Docker
docker compose up research-agent-cpu
```

访问 `http://localhost:8501`

### 6.3 CLI 常用操作

```bash
# 论文处理
python main.py workflow paper --file paper.pdf

# 会议分析
python main.py workflow meeting --audio meeting.wav --title "周会"

# 实验管理
python main.py workflow experiment --name exp1 --dataset ds1 --model resnet50

# 数据集分析
python main.py workflow dataset --root ./data --name DairySheepHR

# 运行 Agent
python main.py agent run --type experiment --goal "对比所有已完成实验的loss"

# 论文导出
python main.py export --type experiment --format latex
python main.py export --type dataset --format markdown
python main.py export --type experiment --format csv

# 点云去重
python main.py dataset dedup --root ./data --voxel-size 0.05 --output dedup_report.md

# 性能测试
python main.py benchmark

# 健康检查
python main.py health

# MCP Server（供 Cursor/Claude 调用）
python main.py mcp-server
```

### 6.4 编程接口

```python
from src.core.agent import ResearchAgent

# 初始化
agent = ResearchAgent("configs/default.yaml")
agent.initialize()

# --- 数据集管理 ---
dm = agent.managers["dataset"]
inventory = dm.scan_dataset("./workspace/datasets/mydata")
stats = dm.get_statistics()
report = dm.generate_report("MyDataset")

# --- 知识库 ---
agent.knowledge_service.index_text(
    source_type="paper",
    text="paper content...",
    metadata={"title": "Paper Title"}
)
results = agent.knowledge_service.search("point cloud segmentation", top_k=5)

# --- Agent ---
coordinator = agent.coordinator
result = coordinator.run_agent(
    agent_type="experiment",
    goal="分析所有实验的 accuracy 趋势"
)
print(result["summary"])
print(result.get("reflection", {}))

# --- 记忆 ---
mem_svc = agent.services["research_memory"]
mem_svc.save_memory(
    category="Research",
    title="重要发现",
    content="Chamfer Distance 阈值 0.01 效果最佳",
    source="Experiment exp_001",
    importance="高"
)
context = mem_svc.get_relevant_context("点云分割参数调优")

# --- 导出 ---
from src.export import LatexExporter, PlotExporter

latex = LatexExporter()
table = latex.export_experiment_table(experiments_list)
latex.save(table, "output/experiments.tex")

plot = PlotExporter()
plot.loss_curve(
    train_loss=[0.9, 0.5, 0.1],
    val_loss=[0.85, 0.55, 0.2],
    output_path="output/loss_curve.png"
)

# --- 去重 ---
from src.dataset.dedup import PointCloudDedupChecker

checker = PointCloudDedupChecker(voxel_size=0.05, chamfer_threshold=0.01)
result = checker.check_directory("./data")
checker.generate_report(result, "dedup_report.md")

# --- Benchmark ---
from src.benchmark.runner import BenchmarkRunner

runner = BenchmarkRunner(agent)
print(runner.report())
```

### 6.5 MCP 集成（Cursor / Claude）

**方式一：直接启动**

```bash
python main.py mcp-server
```

**方式二：在 IDE 中配置**

```json
{
  "mcpServers": {
    "research-agent": {
      "command": "python",
      "args": ["main.py", "mcp-server"],
      "cwd": "/path/to/ResearchAgent"
    }
  }
}
```

配置后，AI 助手可直接调用 24 个 ResearchAgent 工具。

### 6.6 日志

- 日志文件：`logs/research_agent.log`
- 自动轮转：单文件 10MB，保留 3 个备份
- 同时输出到控制台

---

## 7. 扩展开发指南

### 7.1 添加新的 LLM Provider

```python
# src/llm/deepseek_adapter.py
from src.llm.openai_adapter import OpenAIAdapter

class DeepSeekAdapter(OpenAIAdapter):
    @property
    def provider(self) -> str:
        return "deepseek"
```

在 `src/llm/adapter_factory.py` 注册，配置文件添加 provider 配置即可。

### 7.2 添加新的 Agent

```python
# src/agents/custom_agent.py
from src.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def _register_tools(self):
        self._add_tool("my_tool", "My tool description", self._manager.my_method)
```

在 `AgentCoordinator._init_agents()` 中注册。

### 7.3 添加新的 MCP Tool

在 `src/mcp/tools.py` 对应 `_register_*_tools` 函数中添加：

```python
r.register(
    "my_tool_name",
    "Tool description",
    {"type": "object", "properties": {...}, "required": [...]},
    lambda agent, args: _serialize(result),
)
```

### 7.4 添加新的 Workflow

```python
# src/workflows/my_workflow.py
from src.workflows.research_workflow import ResearchWorkflow

class MyWorkflow(ResearchWorkflow):
    def run(self, **kwargs) -> dict:
        # 实现流水线逻辑
        return {"status": "completed"}
```

在 `agent.py` 的 `_register_managers()` 中注册。

### 7.5 添加新的 Exporter

```python
# src/export/json_exporter.py
class JsonExporter:
    def export(self, data: list[dict]) -> str:
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)
```

在 `src/export/__init__.py` 中导出，在 `commands.py` 中添加 CLI 支持。

---

## 8. 附录

### 8.1 快速启动清单

```bash
# 1. 进入项目
cd ResearchAgent

# 2. 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 设置 API Key（LLM 功能需要）
set OPENAI_API_KEY=sk-your-key

# 5. 启动
python main.py web                     # Web UI
python main.py mcp-server              # MCP Server
docker compose up research-agent-cpu   # Docker

# 6. 验证
python main.py health
pytest tests/ -v
```

### 8.2 项目文件树

```text
ResearchAgent/
├── main.py                       # CLI 入口（10 子命令）
├── run_web.py                    # Web UI 启动脚本
├── requirements.txt              # Python 依赖（17 个）
├── Dockerfile                    # 生产环境
├── Dockerfile.dev                # 开发环境
├── docker-compose.yml            # 编排（CPU/GPU/Dev）
├── .dockerignore
│
├── configs/
│   └── default.yaml              # 默认配置
│
├── prompts/                      # Prompt 模板
│   ├── assistant/                # 助手人格/风格
│   ├── dataset/                  # 数据集卡片/报告
│   ├── meeting/                  # 会议分析
│   └── paper/                    # 论文分析
│
├── src/
│   ├── core/agent.py             # ResearchAgent 核心
│   ├── config/                   # 配置管理
│   ├── llm/                      # LLM 适配器
│   ├── embedding/                # Embedding 适配器
│   ├── asr/                      # ASR 适配器
│   ├── vision/                   # Vision 适配器
│   ├── agents/                   # Agent + Coordinator + Reflection
│   ├── reasoning/                # ReAct 推理引擎
│   ├── services/                 # 12 个服务
│   ├── managers/                 # 7 个 Manager
│   ├── persistence/              # 7 个 Repository
│   ├── workflows/                # 5 个 Workflow
│   ├── knowledge/                # RAG (Chunker/Indexer/Retriever/Citation/Reranker)
│   ├── memory/                   # 语义记忆 (SemanticMemoryStore)
│   ├── dataset/                  # 数据集模块 (Scanner/Integrity/Stats/Reporter/Exporter/Dedup)
│   ├── experiment/               # 实验模块
│   ├── tools/                    # 底层工具
│   │   ├── filesystem/           # FileScanner / Checksum
│   │   └── pointcloud/           # PLY/PCD Reader / Statistics
│   ├── export/                   # 学术导出 (LaTeX/Markdown/CSV/Excel/Plot)
│   ├── benchmark/                # 性能基准
│   ├── mcp/                      # MCP Server (Server/Registry/Tools)
│   ├── cli/                      # CLI 命令处理
│   ├── web/                      # Streamlit UI (8 pages)
│   ├── planning/                 # 自动科研规划
│   ├── events/                   # EventBus + Listener
│   ├── health/                   # 健康检查
│   ├── meeting/                  # 会议模块
│   ├── paper/                    # 论文模块
│   ├── utils/                    # 工具类 (Cache/Logging/Exceptions)
│   └── assistant/                # 对话助手
│
├── tests/                        # 301 测试用例
│   ├── fixtures/
│   └── test_*.py                 # 27 个测试文件
│
└── docs/                         # 文档
    ├── Architecture.md
    ├── ProjectProposal.md
    ├── ProductManual_v1.0.md
    ├── ProductManual_v2.0.md      # 本文件
    └── TestChecklist_v1.0.md
```

### 8.3 系统指标

| 指标 | 数值 |
|------|------|
| Python 文件数 | 120+ |
| 测试用例 | 301 |
| MCP Tools | 24 |
| CLI 子命令 | 10 |
| Web 页面 | 8 |
| Manager | 7 |
| Agent | 4 |
| Workflow | 5 |
| Repository | 7 |
| Service | 12 |
| Exporter | 5 |

### 8.4 依赖速查

| 包 | 版本 | 用途 |
|----|------|------|
| openai | >=1.0.0 | LLM/Embedding/Vision/ASR API |
| streamlit | >=1.28.0 | Web UI |
| chromadb | >=0.5.0 | 向量数据库 |
| faster-whisper | >=1.0.0 | 本地语音识别 |
| pypdf | >=5.0.0 | PDF 解析 |
| python-docx | >=1.1.0 | DOCX 解析 |
| pandas | >=2.0.0 | 数据处理 |
| numpy | >=1.24.0 | 数值计算 |
| scipy | >=1.10.0 | cKDTree 点云去重 |
| matplotlib | >=3.7.0 | 图表导出 |
| openpyxl | >=3.1.0 | Excel 导出 |
| pyyaml | >=6.0 | 配置解析 |
| rich | >=13.0.0 | CLI 美化 |
| psutil | >=5.9.0 | 性能监控 |
| torch | >=2.0.0 | GPU 检测 |
| pytest | >=7.0.0 | 测试框架 |
| pytest-mock | >=3.10 | Mock 支持 |

---

> **版本：** v2.0  
> **日期：** 2026-07-13  
> **作者：** ResearchAgent Team
