# ResearchAgent v1.0 功能测试清单

---

## 测试环境准备

### 准备测试数据

在 `workspace/datasets/` 下创建两个测试数据集：

```
workspace/datasets/
├── test_dataset_good/           # 正常数据集
│   ├── sheep_001.ply            # ASCII PLY，100 点
│   ├── sheep_002.ply            # ASCII PLY，200 点
│   ├── sheep_003.pcd            # ASCII PCD，150 点
│   ├── subdir/
│   │   └── sheep_004.ply        # ASCII PLY，50 点
│   └── checksums.md5            # 正确的校验和清单
│
├── test_dataset_broken/         # 异常数据集
│   ├── valid.ply                # 正常 PLY
│   ├── corrupted.ply            # 缺少 end_header 的损坏 PLY
│   ├── not_pointcloud.txt       # 应被过滤的非点云文件
│   └── checksums.md5            # 包含错误 hash 的清单（触发 mismatch）
│
└── test_dataset_empty/          # 空数据集（目录存在但无点云文件）
    └── readme.txt               # 无效文件，应被过滤
```

### 快速生成测试数据（Python 脚本）

```python
# 在 Python 中运行以下代码生成测试数据
from pathlib import Path

base = Path("./workspace/datasets")

# --- test_dataset_good ---
good = base / "test_dataset_good"
good.mkdir(parents=True, exist_ok=True)
(good / "subdir").mkdir(exist_ok=True)

ply_header = "ply\nformat ascii 1.0\nelement vertex {n}\nproperty float x\nproperty float y\nproperty float z\nend_header\n"
pcd_header = "# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH {n}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {n}\nDATA ascii\n"

for name, n in [("sheep_001.ply", 100), ("sheep_002.ply", 200)]:
    with open(good / name, "w") as f:
        f.write(ply_header.format(n=n))
        for i in range(min(n, 5)):
            f.write(f"{i*1.0} {i*2.0} {i*3.0}\n")

for name, n in [("sheep_003.pcd", 150)]:
    with open(good / name, "w") as f:
        f.write(pcd_header.format(n=n))

with open(good / "subdir" / "sheep_004.ply", "w") as f:
    f.write(ply_header.format(n=50))

# 生成 checksums.md5（需要先扫描得到 MD5，此处手动示意）
# 使用 Python hashlib 计算后填入

# --- test_dataset_broken ---
broken = base / "test_dataset_broken"
broken.mkdir(parents=True, exist_ok=True)

with open(broken / "valid.ply", "w") as f:
    f.write(ply_header.format(n=100))

with open(broken / "corrupted.ply", "w") as f:
    f.write("ply\nformat ascii 1.0\nelement vertex 50\n")  # 无 end_header

with open(broken / "not_pointcloud.txt", "w") as f:
    f.write("this is not a point cloud file")

# 构造错误的 checksums.md5
with open(broken / "checksums.md5", "w") as f:
    f.write("00000000000000000000000000000000  valid.ply\n")

# --- test_dataset_empty ---
empty = base / "test_dataset_empty"
empty.mkdir(parents=True, exist_ok=True)
with open(empty / "readme.txt", "w") as f:
    f.write("empty dataset")
```

### 配置 LLM（可选）

- **无 LLM 模式**：不设置 `OPENAI_API_KEY`，测试基础功能
- **有 LLM 模式**：`set OPENAI_API_KEY=sk-your-key`，测试报告生成

---

## 一、启动与导航

| # | 测试项 | 操作步骤 | 预期结果 |
|---|--------|---------|---------|
| 1.1 | Web UI 启动 | 执行 `python run_web.py` | 终端显示 "Starting ResearchAgent Web UI..."，浏览器自动打开 `localhost:8501` |
| 1.2 | 页面标题和图标 | 查看浏览器标签页 | 标题显示 "ResearchAgent"，图标为显微镜 |
| 1.3 | Sidebar 导航 | 查看左侧 sidebar | 显示 "ResearchAgent" 标题 + 两个导航项：Dashboard / Dataset Management |
| 1.4 | 默认进入 Dashboard | 启动后 | 默认显示 Dashboard 页面 |
| 1.5 | 切换页面 | 点击 "Dataset Management" | 页面切换到 Dataset Management |
| 1.6 | 切回 Dashboard | 点击 "Dashboard" | 页面切换回 Dashboard |

---

## 二、Dashboard 页面

| # | 测试项 | 操作步骤 | 预期结果 |
|---|--------|---------|---------|
| 2.1 | 版本号显示 | 查看 System Info | 显示 Version: 0.1.0 |
| 2.2 | Workspace 显示 | 查看 System Info | 显示 Workspace: ./workspace |
| 2.3 | LLM Provider 显示（无 Key） | 未设置 OPENAI_API_KEY | 显示 "Not configured" |
| 2.4 | LLM Provider 显示（有 Key） | 已设置 OPENAI_API_KEY | 显示 "openai" |
| 2.5 | LLM 未配置警告（无 Key） | 查看页面底部 | 显示黄色警告："LLM not configured..." |
| 2.6 | LLM 已配置无警告（有 Key） | 查看页面底部 | 无黄色警告 |
| 2.7 | Manager 列表 | 查看 Managers 区域 | 显示绿色 "Dataset Manager" 标签 |
| 2.8 | Tools 列表 | 查看 Tools 区域 | 显示 5 个工具名：file_scanner, checksum, ply_reader, pcd_reader, pointcloud_statistics |

---

## 三、Dataset Management — 基础操作

| # | 测试项 | 操作步骤 | 预期结果 |
|---|--------|---------|---------|
| 3.1 | 默认路径 | 查看 Dataset Path 输入框 | 显示 `./workspace/datasets` |
| 3.2 | 修改路径 | 输入框改为 `./workspace/datasets/test_dataset_good` | 输入框更新 |
| 3.3 | 扫描正常数据集 | 输入正确路径，点击 "Scan Dataset" | 显示绿色成功消息，列出文件数和总大小 |
| 3.4 | 扫描空数据集 | 输入 `test_dataset_empty`，点击 "Scan Dataset" | 成功，但文件数为 0 |
| 3.5 | 扫描不存在的路径 | 输入不存在的路径，点击 "Scan Dataset" | 显示红色错误消息 |
| 3.6 | 未扫描直接点 Integrity | 不扫描，直接点击 "Check Integrity" | 显示黄色警告 "Scan dataset first." |
| 3.7 | 未扫描直接点 Statistics | 不扫描，直接点击 "Generate Statistics" | 显示黄色警告 "Scan dataset first." |

---

## 四、File List 标签页

| # | 测试项 | 操作步骤 | 预期结果 |
|---|--------|---------|---------|
| 4.1 | 文件列表显示 | 扫描 `test_dataset_good`，切换到 File List | 显示总文件数和大小，展示文件表格（File / Size (KB) / MD5） |
| 4.2 | 文件数量正确 | 查看表格 | 显示 4 个文件（包括子目录中的） |
| 4.3 | PLY 文件被识别 | 查看表格 | sheep_001.ply、sheep_002.ply、subdir/sheep_004.ply 均在列表中 |
| 4.4 | PCD 文件被识别 | 查看表格 | sheep_003.pcd 在列表中 |
| 4.5 | 非点云文件被过滤 | 查看表格 | not_pointcloud.txt 不在列表中 |
| 4.6 | MD5 列截断显示 | 查看表格 MD5 列 | 显示前8位 + "..." |
| 4.7 | 超过 100 文件提示 | （如有 >100 文件的数据集） | 显示 "Showing 100 of N files" |
| 4.8 | 文件大小正确 | 查看 Size (KB) | 每个文件大小合理（非 0、非负） |

---

## 五、Statistics 标签页

| # | 测试项 | 操作步骤 | 预期结果 |
|---|--------|---------|---------|
| 5.1 | 总数统计 | 扫描后点击 "Generate Statistics"，切换到 Statistics | Total Files: 4, Total Size: 显示为 "X.XX MB" |
| 5.2 | 点云文件统计 | 查看 Point Cloud Files | 显示 4（所有文件均为点云文件） |
| 5.3 | 点数范围 | 扫描 `test_dataset_good` 后查看 Stats | Min: 50, Max: 200, Avg: 125.0（或接近值） |
| 5.4 | 文件类型分布 | 查看 File Types JSON | 显示 `{".ply": 3, ".pcd": 1}` |
| 5.5 | 子目录显示 | 查看 Subdirectories | 显示 "- subdir" |
| 5.6 | 空数据集统计 | 扫描 `test_dataset_empty`，查看统计 | Total Files: 0, Point Cloud Files: 0, 点数均为 None |
| 5.7 | 统计结果持久化 | 切换到其他 Tab 再切回 | 统计数据保持显示 |

---

## 六、Integrity 标签页

| # | 测试项 | 操作步骤 | 预期结果 |
|---|--------|---------|---------|
| 6.1 | 完整性通过 | 对 `test_dataset_good` 扫描后，确保 checksums.md5 正确，点击 "Check Integrity" | 绿色 "All checks passed." |
| 6.2 | 无效目录无 manifest | 扫描 `test_dataset_empty`，点击 "Check Integrity" | 绿色 "All checks passed."（无 manifest 视为通过） |
| 6.3 | 校验和不匹配 | 扫描 `test_dataset_broken`（其 checksums.md5 中 valid.ply 的 hash 是错误的），点击 Check Integrity | 红色错误，显示 checksum mismatches 列表 |
| 6.4 | Manifest 中有但目录中无 | 在 checksums.md5 中添加一个不存在的文件名，扫描后检查完整性 | 红色错误，显示 missing files 列表 |
| 6.5 | 扫描文件未在 manifest 中 | 删除 checksums.md5 中的某文件条目 | 显示 warning 级别 issue："File not listed in manifest" |
| 6.6 | Manifest 缺失默认路径 | 数据集目录下没有 checksums.md5，点击 Check Integrity | 通过（跳过检查） |

---

## 七、Report 标签页（需要 LLM）

| # | 测试项 | 操作步骤 | 预期结果 |
|---|--------|---------|---------|
| 7.1 | LLM 未配置时报告 | 不设 OPENAI_API_KEY，扫描后点击 "Generate Report" | 红色错误："LLM not configured..." |
| 7.2 | LLM 未配置时 Card | 不设 OPENAI_API_KEY，点击 "Generate Dataset Card" | 红色错误："LLM not configured..." |
| 7.3 | 生成报告 | 设置 OPENAI_API_KEY，扫描后输入 Dataset Name，点击 "Generate Report" | Loading 后显示 Markdown 格式的中文报告，包含 Overview/Statistics/Integrity/Suggestions |
| 7.4 | 报告命名默认值 | 不输入 Dataset Name 直接生成报告 | 数据集名默认为目录名（如 test_dataset_good） |
| 7.5 | 生成 Dataset Card | 扫描后点击 "Generate Dataset Card" | Loading 后显示黄色成功消息，路径指向数据集目录，展示完整 Markdown Card |
| 7.6 | Dataset Card 文件落盘 | 生成 Card 后检查数据集目录 | `DATASET_CARD.md` 文件存在，内容与页面显示一致 |
| 7.7 | 报告内容完整性 | 查看生成的报告 | 包含文件统计、点云信息、完整性结果等真实数据，非占位符 |
| 7.8 | 切换页面后结果保留 | 生成报告后切换到 Dashboard 再切回 | 报告的 Markdown 仍在 Report 标签中显示 |

---

## 八、边界与异常测试

| # | 测试项 | 操作步骤 | 预期结果 |
|---|--------|---------|---------|
| 8.1 | 损坏的 PLY 文件 | 扫描包含 `corrupted.ply` 的数据集 | 扫描成功，但统计时该文件被跳过（不崩溃） |
| 8.2 | 混合有效无效文件 | 扫描 `test_dataset_broken`，查看文件列表和统计 | valid.ply 正确统计，corrupted.ply 在文件列表中但点数为 0（跳过） |
| 8.3 | 路径包含中文 | 创建中文路径目录，放入 PLY 文件，扫描 | 正常扫描，不崩溃 |
| 8.4 | 路径包含空格 | 创建含空格路径目录，扫描 | 正常扫描 |
| 8.5 | 无 .ply/.pcd 的数据集 | 扫描 `test_dataset_empty` | 文件列表为空，统计全为 0/None |
| 8.6 | 多次反复扫描 | 先扫描 A 目录，再扫描 B 目录，查看 File List | 显示 B 目录的文件（覆盖之前的 session state） |
| 8.7 | 浏览器刷新 | 在 Dataset 页面按 F5 刷新 | 页面重建，之前的 session_state 丢失，需要重新扫描 |
| 8.8 | Sidebar 导航不丢 Agent | 反复在 Dashboard 和 Dataset 间切换 | Agent 不被重新初始化（`@st.cache_resource` 生效） |
| 8.9 | 并发操作顺序 | 先点 Scan，Loading 期间点 Check Integrity | Check Integrity 按钮跳过或等待（取决于 Streamlit 渲染） |

---

## 九、日志文件验证

| # | 测试项 | 操作步骤 | 预期结果 |
|---|--------|---------|---------|
| 9.1 | 日志文件生成 | 启动 Web UI 后查看 `logs/` 目录 | `research_agent.log` 文件存在 |
| 9.2 | 初始化日志 | 查看日志文件内容 | 包含 "Logging initialized"、"LLM provider: openai"（或 warning）、"Dataset Manager initialized" |
| 9.3 | 操作日志 | 执行扫描操作后查看日志 | 包含 "Scanning dataset"、"Scan complete" |
| 9.4 | 错误日志 | 扫描不存在的路径后查看日志 | 包含异常信息 |

---

## 快速测试顺序（推荐）

按以下顺序执行，约 15-20 分钟完成核心验证：

1. **启动** → `python run_web.py`，确认页面打开（1.1-1.6）
2. **Dashboard** → 检查版本、Provider、Manager、Tools（2.1-2.8）
3. **切换** → 进入 Dataset Management（1.5）
4. **扫描正常集** → 输入 `test_dataset_good`，点击 Scan Dataset（3.3）
5. **检查 File List** → 验证文件表格（4.1-4.6）
6. **统计** → 点击 Generate Statistics，切换到 Statistics Tab 验证（5.1-5.5）
7. **完整性** → 点击 Check Integrity，切换到 Integrity Tab 验证（6.1）
8. **扫描异常集** → 改路径为 `test_dataset_broken`，Scan（8.1-8.2）
9. **完整性失败** → Check Integrity，验证 mismatch 提示（6.3）
10. **空集** → 改路径为 `test_dataset_empty`，Scan + Statistics（3.4, 5.6）
11. **不存在的路径** → 输入随机路径，Scan，验证错误消息（3.5）
12. **生成报告** → 切回 `test_dataset_good`，Scan 后在 Report Tab 生成（7.3-7.4）
13. **生成 Card** → 生成 Dataset Card，验证文件落盘（7.5-7.6）
14. **日志** → 查看 `logs/research_agent.log`（9.1-9.4）
