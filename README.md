# ResearchAgent — AI 科研助手

面向 **DairySheepHR** 项目的智能科研助手系统，提供论文分析、会议记录、实验管理、数据集管理等一站式科研工作流支持。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API 密钥
export OPENAI_API_KEY="your-api-key"

# 启动 Web 界面
python main.py web

# 运行论文分析工作流
python main.py workflow paper --file paper.pdf

# 查看所有命令
python main.py --help
```

## 系统架构

```
ResearchAgent/
├── main.py                   # CLI 主入口（9个子命令）
├── run_web.py                # Streamlit Web 启动
├── src/
│   ├── core/agent.py         # 核心编排器（依赖注入容器）
│   ├── config/               # YAML 配置管理，支持 ${ENV_VAR}
│   ├── llm/                  # LLM 适配器（OpenAI / DeepSeek）
│   ├── reasoning/            # ReAct 推理引擎（思考→行动→观察）
│   ├── agents/               # 领域 Agent（论文/会议/实验/数据集/反思）
│   ├── services/             # 服务层（LLM/ASR/嵌入/知识库/报告）
│   ├── knowledge/            # 知识库（ChromaDB + 重排序 + 引用管理）
│   ├── persistence/          # SQLite 持久化（对话/会议/论文/实验/记忆）
│   ├── managers/             # 业务逻辑管理器
│   ├── workflows/            # 自动化工作流编排
│   ├── mcp/                  # MCP 服务器（Model Context Protocol）
│   ├── vision/               # 视觉分析（OpenAI Vision / CLIP）
│   ├── asr/                  # 语音识别（Whisper 本地 / OpenAI）
│   ├── tools/                # 工具集（文件读取/点云分析/文件系统）
│   └── web/                  # Streamlit Web UI
└── tests/                    # 242 个测试通过
```

## 核心功能

### 多领域智能 Agent

| Agent | 功能 | 工具示例 |
|-------|------|---------|
| PaperAgent | 论文导入与分析 | 提取引用、生成摘要、文献综述 |
| MeetingAgent | 会议转录与分析 | 音频转录、摘要生成、行动项提取 |
| ExperimentAgent | 实验生命周期管理 | 创建实验、记录指标、生成报告 |
| DatasetAgent | 数据集管理 | 扫描、去重、完整性检查、Dataset Card |

### 知识库（RAG）

- **ChromaDB** 向量数据库，支持持久化和多集合
- **重排序（Reranker）**：cross-encoder 模型提升检索精度
- **多模态索引**：支持文本 + 图像的联合索引
- **自动索引**：论文/会议/实验创建时自动入库

### ReAct 推理引擎

```
用户目标 → [思考] → [选择工具] → [执行操作] → [观察结果] → 循环 → 最终答案
```

- JSON 格式的工具调用协议
- 最大迭代次数控制，防止无限循环
- 可选的反思机制，自我评估输出质量

### 工作流

```bash
# 论文全流程：读取 → 分析 → 索引 → 提取任务
research-agent workflow paper --file paper.pdf

# 会议全流程：转录/文本 → 分析 → 索引 → 提取待办
research-agent workflow meeting --audio meeting.wav --title "周会"

# 实验全流程：创建 → 记录指标 → 报告 → 索引
research-agent workflow experiment --name "Exp01" --dataset DS

# 批量自动索引
research-agent workflow auto-index

# 数据集分析全流程
research-agent workflow dataset --root ./data --name "MyDataset"
```

### MCP 服务器

与 Claude Desktop / VS Code 等 MCP 客户端集成：

```json
{
  "mcpServers": {
    "research-agent": {
      "command": "python",
      "args": ["main.py", "mcp-server"]
    }
  }
}
```

### Web 界面

启动 Streamlit Web UI，提供图形化的助手交互、数据集管理和知识库检索：

```bash
python main.py web
# 或
streamlit run src/web/app.py
```

## 配置

配置文件位于 `configs/default.yaml`，支持环境变量占位符：

```yaml
llm:
  default_provider: deepseek
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      base_url: "https://api.openai.com/v1"
      model: gpt-4o
    deepseek:
      api_key: ${OPENAI_API_KEY}
      base_url: "https://api.deepseek.com/v1"
      model: deepseek-chat

knowledge:
  persist_dir: ./workspace/chroma_db
  reranker_model: cross-encoder/ms-marco-MiniLM-L-6-v2

cache:
  embedding: false
  llm: false
  chroma: false
```

## 运行测试

```bash
pytest tests/ -v                          # 全部测试
pytest tests/test_agents.py -v            # Agent 测试
pytest tests/test_knowledge.py -v         # 知识库测试
pytest tests/test_phase4_integration.py   # 集成测试
```

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | OpenAI API / DeepSeek（兼容协议） |
| 嵌入 | OpenAI Embedding / Sentence Transformers / CLIP |
| 语音识别 | OpenAI Whisper / Local Whisper |
| 视觉 | OpenAI Vision / CLIP |
| 向量数据库 | ChromaDB |
| 重排序 | Cross-Encoder (ms-marco-MiniLM) |
| 持久化 | SQLite |
| Web 界面 | Streamlit |
| 测试 | Pytest (242 passed) |

## License

MIT
