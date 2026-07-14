# ResearchAgent v1.0 产品说明书

---

## 目录

1. [产品概述](#1-产品概述)
2. [系统架构](#2-系统架构)
3. [功能清单](#3-功能清单)
4. [接口文档](#4-接口文档)
5. [配置说明](#5-配置说明)
6. [使用指南](#6-使用指南)
7. [扩展开发指南](#7-扩展开发指南)
8. [已知限制与后续计划](#8-已知限制与后续计划)

---

## 1. 产品概述

ResearchAgent 是一个面向科学研究全过程的智能体平台，v1.0 聚焦于**三维点云数据集管理**。以大语言模型（LLM）为智能核心，结合专业点云处理工具，实现数据集扫描、完整性检查、统计分析和自动报告生成。

### 1.1 核心能力

- 多格式点云文件扫描与管理（PLY、PCD、PTS、XYZ、XYZRGB、NPY）
- 数据集完整性校验（MD5/SHA256 checksum 比对）
- 点云统计（点数、文件数、格式分布、子目录结构）
- 基于 LLM 自动生成 Dataset Report 和 Dataset Card
- Web UI（Streamlit）交互操作
- 可插拔 LLM 架构，支持 OpenAI 及兼容 API（DeepSeek 等）

### 1.2 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.10 |
| LLM 后端 | OpenAI API（可替换） |
| Web UI | Streamlit 1.59 |
| 配置 | YAML + 环境变量注入 |
| 日志 | Python logging + RotatingFileHandler |
| 测试 | pytest（31 用例） |

---

## 2. 系统架构

### 2.1 架构分层

```text
┌─────────────────────────────────┐
│          Web UI (Streamlit)     │
├─────────────────────────────────┤
│         ResearchAgent            │
├───────────┬─────────────────────┤
│ Managers  │ DatasetManager       │
├───────────┼──────────┬──────────┤
│ Services  │ LLM      │ Prompt   │ Memory │
├───────────┼──────────┼──────────┼────────┤
│ Adapters  │ OpenAI   │ (DeepSeek...将来) │
├───────────┼──────────┴──────────┴────────┤
│ Tools     │ FileScanner│ Checksum│ PLY/PCD│
├───────────┼──────────────────────────────┤
│ Core      │ Config │ Logging │ Exception │
└───────────┴──────────────────────────────┘
```

### 2.2 模块职责

| 层级 | 职责 | 说明 |
|------|------|------|
| Core | 应用入口、配置管理、日志 | `ResearchAgent` 类负责整体生命周期 |
| Adapters | LLM 抽象与适配 | `BaseLLMAdapter` 定义接口，`OpenAIAdapter` 实现 |
| Services | 能力封装 | `LLMService`、`PromptService`、`MemoryService` |
| Tools | 底层功能 | 文件扫描、校验和、点云头解析、统计 |
| Managers | 业务编排 | `DatasetManager` 编排扫描→校验→统计→报告全流程 |
| Web | 用户界面 | Streamlit Dashboard + Dataset Management |

---

## 3. 功能清单

### 3.1 Dataset Management（数据集管理）

| 功能 | 描述 | 需要 LLM |
|------|------|----------|
| 数据集扫描 | 遍历目录，收集文件名、大小、MD5、扩展名 | 否 |
| 完整性检查 | 与 checksum manifest 比对，检测缺失/不匹配文件 | 否 |
| 数据统计 | 文件数、大小、扩展名分布、点云点数（最小/最大/平均） | 否 |
| Dataset Report 生成 | 基于统计结果，调用 LLM 生成详细 Markdown 报告 | 是 |
| Dataset Card 生成 | 调用 LLM 生成 HuggingFace 规范 Dataset Card | 是 |

### 3.2 Web UI

| 页面 | 功能 |
|------|------|
| Dashboard | 显示 Agent 版本、LLM Provider、Workspace、Manager 列表、Tools 列表 |
| Dataset Management | 路径输入、扫描按钮、完整性检查、统计展示、报告生成、Dataset Card 导出 |

### 3.3 日志系统

- 日志文件：`logs/research_agent.log`
- 自动轮转：单文件 10MB，保留 3 个备份
- 同时输出到控制台

---

## 4. 接口文档

### 4.1 ResearchAgent（核心入口）

**所在文件：** `src/core/agent.py`

```python
class ResearchAgent:
    def __init__(self, config_path: str = None)
    def initialize(self) -> None
```

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `config` | `ConfigManager` | 配置管理器 |
| `logger` | `logging.Logger` | 日志实例（名称：ResearchAgent） |
| `llm_service` | `LLMService \| None` | LLM 服务（未配置时为 None） |
| `services` | `dict` | 服务字典：`{"llm", "prompt", "memory"}` |
| `tools` | `dict` | 工具字典：`{"file_scanner", "checksum", "ply_reader", "pcd_reader", "pointcloud_statistics"}` |
| `managers` | `dict` | Manager 字典：`{"dataset": DatasetManager}` |

**使用示例：**

```python
from src.core.agent import ResearchAgent

agent = ResearchAgent()          # 使用默认配置 configs/default.yaml
agent.initialize()               # 启动所有 Manager

# 访问 Dataset Manager
dataset_mgr = agent.managers["dataset"]
inventory = dataset_mgr.scan_dataset("./workspace/datasets/my_dataset")
stats = dataset_mgr.get_statistics()
report = dataset_mgr.generate_report("MyDataset")
```

### 4.2 ConfigManager

**所在文件：** `src/config/config_manager.py`

```python
class ConfigManager:
    def __init__(self, config_path: str = None)
    def get(self, key_path: str, default=None) -> Any
```

**`get()` 方法支持点号分隔路径访问：**

```python
config.get("llm.providers.openai.model")   # → "gpt-4o"
config.get("dataset.root_dir")             # → "./workspace/datasets"
config.get("nonexistent", "fallback")      # → "fallback"
```

**`${ENV_VAR}` 自动解析：**

配置中 `${OPENAI_API_KEY}` 会自动读取环境变量，若未设置则抛出 `ConfigError`。

### 4.3 BaseLLMAdapter（LLM 适配器接口）

**所在文件：** `src/llm/base_adapter.py`

```python
class BaseLLMAdapter(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], **kwargs) -> str: ...

    @abstractmethod
    def chat_stream(self, messages: list[dict], **kwargs) -> Iterator[str]: ...

    @property
    @abstractmethod
    def provider(self) -> str: ...
```

**messages 格式（OpenAI 标准）：**

```python
[
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "帮我分析这个数据集"},
]
```

### 4.4 OpenAIAdapter

**所在文件：** `src/llm/openai_adapter.py`

```python
class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-4o", temperature: float = 0.3,
                 max_tokens: int = 4096)
```

**`chat()` 和 `chat_stream()` 的 `**kwargs` 支持覆盖 `temperature` 和 `max_tokens`。**

错误处理：所有 `openai.OpenAIError` 包装为 `LLMError`。

### 4.5 create_llm_adapter（适配器工厂）

**所在文件：** `src/llm/adapter_factory.py`

```python
def create_llm_adapter(config) -> BaseLLMAdapter
```

- 读取 `config.get("llm.default_provider")` 确定 provider
- 从 `config.get(f"llm.providers.{provider}")` 读取 provider 配置
- 根据 provider 名称创建对应的 Adapter 实例

### 4.6 LLMService

**所在文件：** `src/services/llm_service.py`

```python
class LLMService:
    def __init__(self, adapter: BaseLLMAdapter)
    def chat(self, messages: list[dict], **kwargs) -> str
    def chat_stream(self, messages: list[dict], **kwargs) -> Iterator[str]

    @property
    def provider(self) -> str
    @property
    def total_tokens(self) -> int
```

### 4.7 PromptService

**所在文件：** `src/services/prompt_service.py`

```python
class PromptService:
    def __init__(self, prompts_dir: str = None)
    def load(self, name: str) -> str
    def render(self, name: str, **kwargs) -> str
    def reload(self, name: str = None)
```

**使用示例：**

```python
prompt_service = PromptService()
# 加载并渲染 prompts/dataset/dataset_report.md 模板
content = prompt_service.render("dataset/dataset_report.md",
    dataset_name="MyDataset",
    total_files=100,
    ...
)
```

### 4.8 MemoryService

**所在文件：** `src/services/memory_service.py`

```python
class MemoryService:
    def save(self, key: str, value: str) -> None
    def load(self, key: str) -> str | None
    def query(self, query: str) -> list[str]
    def clear(self) -> None
```

v1.0 使用内存字典实现，后续将扩展为持久化存储 + 语义检索。

### 4.9 DatasetManager

**所在文件：** `src/managers/dataset_manager.py`

```python
class DatasetManager(BaseManager):
    def scan_dataset(self, root_path: str = None) -> DatasetInventory
    def check_integrity(self, manifest_path: str = None) -> IntegrityReport
    def get_statistics(self) -> DatasetStats
    def generate_report(self, dataset_name: str = None) -> str
    def generate_dataset_card(self, dataset_name: str = None, version: str = "1.0.0") -> str

    @property
    def inventory(self) -> DatasetInventory | None
    @property
    def statistics(self) -> DatasetStats | None
    @property
    def integrity_report(self) -> IntegrityReport | None
```

**完整工作流：**

```text
scan_dataset()             →  返回 DatasetInventory
    ↓
check_integrity()          →  返回 IntegrityReport
    ↓
get_statistics()           →  返回 DatasetStats
    ↓
generate_report()          →  返回 Markdown 报告文本
    ↓
generate_dataset_card()    →  保存 DATASET_CARD.md 到数据集目录
```

**调用顺序要求：** `check_integrity()`、`get_statistics()`、`generate_report()`、`generate_dataset_card()` 必须在 `scan_dataset()` 之后调用，否则抛出 `RuntimeError`。

### 4.10 数据模型

**所在文件：** `src/dataset/models.py`

```python
@dataclass
class FileEntry:
    relative_path: str          # 相对路径
    absolute_path: str          # 绝对路径
    size_bytes: int             # 文件大小（字节）
    extension: str              # 扩展名（小写）
    md5_hex: str | None         # MD5 哈希

@dataclass
class DatasetInventory:
    root_path: str              # 数据集根目录
    files: list[FileEntry]      # 文件列表
    total_files: int            # 总文件数
    total_size_bytes: int       # 总大小（字节）
    extension_counts: dict[str, int]  # 各扩展名文件数

@dataclass
class IntegrityIssue:
    severity: str               # "error" | "warning"
    file_path: str              # 文件路径
    message: str                # 问题描述

@dataclass
class IntegrityReport:
    passed: bool                # 是否通过
    issues: list[IntegrityIssue]
    missing_files: list[str]    # 缺失文件
    checksum_mismatches: list[str]  # 校验和不匹配文件

@dataclass
class DatasetStats:
    total_files: int
    total_size_human: str       # 人类可读大小（如 "1.5 GB"）
    extensions: dict[str, int]  # 扩展名→数量
    point_cloud_files: int      # 点云文件总数
    ply_files: int              # PLY 文件数
    pcd_files: int              # PCD 文件数
    avg_point_count: float | None
    min_point_count: int | None
    max_point_count: int | None
    subdirectories: list[str]   # 子目录列表
```

### 4.11 BaseTool（工具基类）

**所在文件：** `src/tools/base_tool.py`

```python
class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def run(self, **kwargs): ...
```

**已实现的工具：**

| 工具名称 | 类名 | 功能 |
|----------|------|------|
| `file_scanner` | `FileScanner` | 扫描目录，按扩展名过滤文件 |
| `checksum` | `ChecksumTool` | 计算/验证 MD5/SHA256 |
| `ply_reader` | `PLYReader` | 解析 PLY 头获取点数 |
| `pcd_reader` | `PCDReader` | 解析 PCD 头获取点数 |
| `pointcloud_statistics` | `PointCloudStatistics` | 统计目录内点云文件信息 |

### 4.12 BaseManager

**所在文件：** `src/managers/base_manager.py`

```python
class BaseManager:
    def __init__(self, name: str, agent=None)
    def initialize(self) -> None

    @property   def llm(self)      # → agent.llm_service
    @property   def tools(self)     # → agent.tools
    @property   def config(self)    # → agent.config
    @property   def logger(self)    # → agent.logger
    @property   def services(self)  # → agent.services
```

### 4.13 异常层级

**所在文件：** `src/utils/exceptions.py`

```text
ResearchAgentError (Exception)
├── ConfigError        — 配置文件错误（文件缺失、环境变量未设置）
├── LLMError           — LLM API 调用错误
├── ToolError          — 工具执行错误
└── ManagerError       — Manager 级别错误
```

---

## 5. 配置说明

### 5.1 配置文件

**默认路径：** `configs/default.yaml`

```yaml
agent:
  name: ResearchAgent         # Agent 名称
  version: "0.1.0"            # 版本号
  workspace_dir: "./workspace" # 工作空间目录

llm:
  default_provider: openai    # 默认 LLM provider
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}           # 从环境变量读取
      base_url: https://api.openai.com/v1  # API 地址（兼容 DeepSeek）
      model: gpt-4o                         # 模型名称
      temperature: 0.3                      # 温度（0-1）
      max_tokens: 4096                      # 最大输出 token

dataset:
  root_dir: "./workspace/datasets"          # 默认数据集目录
  allowed_extensions:                       # 允许的文件扩展名
    - .ply    # Polygon File Format
    - .pcd    # Point Cloud Data
    - .pts    # Point Set
    - .xyz    # XYZ coordinates
    - .xyzrgb # XYZ + RGB
    - .npy    # NumPy binary

logging:
  level: INFO                  # DEBUG/INFO/WARNING/ERROR
  log_dir: "./logs"            # 日志目录
  max_bytes_per_file: 10485760 # 单文件 10MB 轮转
  backup_count: 3              # 保留 3 个备份

web:
  host: localhost              # Streamlit 绑定地址
  port: 8501                   # Streamlit 端口
```

### 5.2 环境变量

| 变量 | 用途 | 必需 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | 使用 LLM 功能时必需 |

### 5.3 使用自定义配置

```bash
# CLI 模式
python main.py --config /path/to/custom.yaml

# Python API
agent = ResearchAgent(config_path="/path/to/custom.yaml")
```

---

## 6. 使用指南

### 6.1 环境准备

```bash
# 1. 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\activate   # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置环境变量（如需 LLM 功能）
set OPENAI_API_KEY=sk-your-api-key   # Windows
# export OPENAI_API_KEY=sk-your-api-key  # Linux/Mac
```

### 6.2 命令行模式

```bash
python main.py

# 输出：
# =============================================
#         ResearchAgent v0.1.0
# =============================================
# [Manager] Dataset Manager initialized.
# System Ready.
```

### 6.3 Web UI 模式

```bash
# 方式一：一键启动
python run_web.py

# 方式二：直接调用 Streamlit
streamlit run src/web/app.py
```

浏览器打开 `http://localhost:8501`。

### 6.4 Web UI 操作流程

**Dashboard 页面：**
- 查看系统状态：版本号、LLM Provider、Workspace
- 查看已注册 Manager 和 Tools

**Dataset Management 页面：**

1. **输入数据集路径**（默认 `./workspace/datasets`）
2. **点击 Scan Dataset** → 扫描所有点云文件
3. **点击 Check Integrity** → 与 checksums.md5 比对（可选）
4. **点击 Generate Statistics** → 查看文件统计和点云信息
5. **切换到 Report 标签** → 点击 Generate Report 生成 LLM 报告
6. **点击 Generate Dataset Card** → 在数据集目录生成 `DATASET_CARD.md`

### 6.5 编程接口使用

```python
from src.core.agent import ResearchAgent

# 初始化
agent = ResearchAgent()
agent.initialize()

# 获取 Dataset Manager
dm = agent.managers["dataset"]

# 扫描数据集
inventory = dm.scan_dataset("D:/data/my_pointclouds")
print(f"总文件数: {inventory.total_files}")
print(f"总大小: {inventory.total_size_bytes} bytes")

# 完整性检查
report = dm.check_integrity()
if report.passed:
    print("完整性检查通过")
else:
    print(f"发现问题: {report.missing_files}")

# 统计
stats = dm.get_statistics()
print(f"点云文件: {stats.point_cloud_files}")
print(f"点数范围: {stats.min_point_count} - {stats.max_point_count}")

# 生成 LLM 报告（需要配置 OPENAI_API_KEY）
if agent.llm_service:
    report_text = dm.generate_report("MyDataset")
    print(report_text)

    # 生成 Dataset Card
    card_path = dm.generate_dataset_card("MyDataset", version="1.0")
    print(f"Dataset Card 已保存至: {card_path}")
```

### 6.6 Checksum Manifest 格式

在数据集目录下创建 `checksums.md5` 文件：

```text
# 注释行以 # 开头
5eb63bbbe01eeed093cb22bb8f5acdc3  sample.ply
d41d8cd98f00b204e9800998ecf8427f  subdir/data.ply
```

格式：`<MD5_HASH>  <相对路径>`（以空格分隔）

---

## 7. 扩展开发指南

### 7.1 添加新的 LLM Provider

以添加 DeepSeek 为例：

**Step 1：创建 Adapter**

```python
# src/llm/deepseek_adapter.py
from src.llm.base_adapter import BaseLLMAdapter
from src.llm.openai_adapter import OpenAIAdapter  # DeepSeek 兼容 OpenAI API

class DeepSeekAdapter(OpenAIAdapter):
    @property
    def provider(self) -> str:
        return "deepseek"
```

**Step 2：在工厂中注册**

```python
# src/llm/adapter_factory.py
from src.llm.deepseek_adapter import DeepSeekAdapter

def create_llm_adapter(config):
    # ...已有代码...
    elif provider == "deepseek":
        return DeepSeekAdapter(
            api_key=provider_config["api_key"],
            base_url=provider_config.get("base_url", "https://api.deepseek.com/v1"),
            model=provider_config["model"],
            temperature=provider_config.get("temperature", 0.3),
            max_tokens=provider_config.get("max_tokens", 4096),
        )
```

**Step 3：添加配置**

```yaml
# configs/default.yaml
llm:
  default_provider: deepseek
  providers:
    deepseek:
      api_key: ${DEEPSEEK_API_KEY}
      base_url: https://api.deepseek.com/v1
      model: deepseek-chat
      temperature: 0.3
      max_tokens: 4096
```

### 7.2 添加新的 Tool

```python
# src/tools/my_tool.py
from src.tools.base_tool import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "我的自定义工具"

    def run(self, **kwargs):
        # 实现逻辑
        return result
```

在 `agent.py` 的 `__init__` 中注册：

```python
from src.tools.my_tool import MyTool

self.tools["my_tool"] = MyTool()
```

### 7.3 添加新的 Manager

```python
# src/managers/my_manager.py
from src.managers.base_manager import BaseManager

class MyManager(BaseManager):
    def __init__(self, agent=None):
        super().__init__("My Manager", agent=agent)

    def initialize(self):
        super().initialize()
        # 初始化自己的资源

    def do_something(self):
        # 通过 self.llm, self.tools, self.config 访问共享资源
        pass
```

在 `agent.py` 中注册：

```python
from src.managers.my_manager import MyManager

def _register_managers(self):
    self.managers["dataset"] = DatasetManager(agent=self)
    self.managers["my_manager"] = MyManager(agent=self)
```

### 7.4 添加新的 Prompt 模板

在 `prompts/` 目录下创建 Markdown 文件，使用 Python `str.format()` 语法：

```markdown
# prompts/my_prompt.md
数据集名称: {dataset_name}
文件数: {total_files}
```

使用：

```python
prompt_service.render("my_prompt.md", dataset_name="test", total_files=100)
```

---

## 8. 已知限制与后续计划

### 8.1 v1.0 已知限制

| 限制 | 说明 | 影响 |
|------|------|------|
| Memory 仅内存存储 | `MemoryService` 使用 dict，重启后丢失 | 低（Phase 2 实现持久化） |
| Meeting Manager 未实现 | 仅有骨架代码 | 无（Phase 2 实现） |
| Paper/Experiment Agent 未实现 | `knowledge/`、`workflows/` 目录为空 | 无（Phase 2 实现） |
| Token 统计为估算 | 使用词数而非实际 tokenizer | 低（仅用于内部计数） |
| PLY/PCD 仅读头 | 不解析点数据，仅统计点数 | 低（v1.0 需求满足） |
| 仅支持 OpenAI 及兼容 API | 其他模型需自行实现 Adapter | 低（架构支持扩展） |
| CLI 仅打印 banner | CLI 无交互式功能 | 低（主要使用 Web UI） |

### 8.2 Phase 2 规划

- **Meeting Agent**：录音转文字（Whisper）、会议摘要、TODO 提取、周报生成
- **Paper Agent**：PDF 解析、创新点提取、Related Work 整理
- **Experiment Agent**：实验参数管理、Loss/MAE 追踪、实验报告
- **Memory 持久化**：SQLite/向量数据库存储
- **Task Planner**：任务调度与依赖管理
- **RAG 知识库**：论文/文档检索增强生成

---

## 附录 A：项目文件树

```text
ResearchAgent/
├── main.py                    # CLI 入口
├── run_web.py                 # Web UI 启动脚本
├── requirements.txt           # Python 依赖
│
├── configs/
│   └── default.yaml           # 默认配置
│
├── prompts/
│   └── dataset/
│       ├── dataset_report.md  # 数据集报告 Prompt
│       └── dataset_card.md    # Dataset Card Prompt
│
├── src/
│   ├── core/
│   │   └── agent.py           # ResearchAgent 核心类
│   ├── config/
│   │   ├── __init__.py
│   │   └── config_manager.py  # 配置管理器
│   ├── llm/
│   │   ├── base_adapter.py    # LLM 适配器抽象接口
│   │   ├── openai_adapter.py  # OpenAI 适配器
│   │   └── adapter_factory.py # 适配器工厂
│   ├── services/
│   │   ├── llm_service.py     # LLM 服务封装
│   │   ├── prompt_service.py  # Prompt 模板服务
│   │   └── memory_service.py  # 记忆服务
│   ├── managers/
│   │   ├── base_manager.py    # Manager 基类
│   │   ├── dataset_manager.py # 数据集 Manager
│   │   └── meeting_manager.py # 会议 Manager（预留）
│   ├── dataset/
│   │   ├── models.py          # 数据模型
│   │   ├── scanner.py         # 数据集扫描
│   │   ├── integrity.py       # 完整性检查
│   │   ├── statistics.py      # 统计生成
│   │   ├── reporter.py        # 报告生成
│   │   └── exporter.py        # Dataset Card 导出
│   ├── tools/
│   │   ├── base_tool.py       # 工具基类
│   │   ├── filesystem/
│   │   │   ├── scanner.py     # 文件扫描
│   │   │   └── checksum.py    # 校验和
│   │   └── pointcloud/
│   │       ├── ply_reader.py  # PLY 读取
│   │       ├── pcd_reader.py  # PCD 读取
│   │       └── statistics.py  # 点云统计
│   ├── utils/
│   │   ├── logging_config.py  # 日志配置
│   │   └── exceptions.py      # 异常定义
│   └── web/
│       ├── app.py             # Streamlit 入口
│       ├── session.py         # Agent 会话管理
│       └── pages/
│           ├── home.py        # Dashboard
│           └── dataset.py     # Dataset 管理页
│
├── docs/
│   ├── Architecture.md        # 架构设计
│   ├── ProjectProposal.md     # 项目提案
│   └── ProductManual_v1.0.md  # 本文件
│
└── tests/
    ├── test_config_manager.py
    ├── test_llm_adapter.py
    ├── test_file_tools.py
    ├── test_pointcloud_tools.py
    ├── test_dataset_manager.py
    └── fixtures/
        └── sample_dataset/    # 测试用数据集
```

---

## 附录 B：快速启动清单

```bash
# 1. 克隆/进入项目
cd ResearchAgent

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 设置 API Key（可选，LLM 功能需要）
set OPENAI_API_KEY=sk-your-key

# 5. 启动 Web UI
python run_web.py

# 6. 运行测试
pytest tests/ -v
```

---

> **版本：** v1.0  
> **日期：** 2026-07-10  
> **作者：** ResearchAgent Team
