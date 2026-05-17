<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Stable-brightgreen.svg" alt="Status">
</p>

<p align="center">
  <a href="#简体中文">简体中文</a> | 
  <a href="#繁體中文">繁體中文</a> | 
  <a href="#english">English</a>
</p>

---

<a name="简体中文"></a>
# 🎬 AgentReplay

**轻量级 AI Agent 执行轨迹回放与分析引擎**

## 🎉 项目介绍

AgentReplay 是一个专为 AI Agent 开发者设计的执行轨迹录制、回放与分析工具。它可以帮助你：

- 🔍 **完整记录** AI Agent 的决策过程、工具调用、Token 消耗
- 📼 **灵活回放** 支持逐步/快速回放，精准定位问题节点
- 📊 **智能分析** 自动分析执行效率、决策质量、资源消耗
- 🔄 **差异对比** 对比不同执行轨迹，发现优化空间

**自研差异化亮点**：
- ✅ 零依赖纯 Python 实现，开箱即用
- ✅ 支持 Claude Code、Cursor、Codex、Windsurf 等多框架格式
- ✅ 多格式报告导出（JSON/Markdown/HTML/CSV）
- ✅ 轻量级设计，单文件即可运行

## ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🎥 **轨迹录制** | 实时记录 Agent 执行过程，支持思考、工具调用、决策、错误等事件类型 |
| 📼 **轨迹回放** | 支持实时/快速/逐步回放模式，可设置断点调试 |
| 📊 **智能分析** | 自动统计耗时、Token 消耗、成功率、工具使用频率等指标 |
| 🔧 **多框架支持** | 兼容 Claude Code、Cursor、Codex、Windsurf、Copilot 等主流框架 |
| 📤 **多格式导出** | 支持 JSON、Markdown、HTML、CSV 等格式导出分析报告 |
| 🎯 **零依赖** | 纯 Python 实现，无需安装任何第三方依赖 |

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 无需额外依赖

### 安装

```bash
# 从 PyPI 安装（推荐）
pip install agentreplay

# 或从源码安装
git clone https://github.com/gitstq/AgentReplay.git
cd AgentReplay
pip install -e .
```

### 基本使用

```python
from agentreplay import TraceRecorder, TraceAnalyzer, AgentFramework

# 1. 创建录制器
recorder = TraceRecorder(
    agent_name="MyAgent",
    framework=AgentFramework.CLAUDE_CODE
)

# 2. 开始录制
recorder.start_trace("分析代码并提供建议")

# 3. 记录执行过程
recorder.start_step("读取文件")
recorder.record_thinking("需要先读取文件内容...", tokens_used=15)
recorder.record_tool_call("Read", {"file_path": "main.py"}, duration_ms=50)
recorder.record_tool_result("Read", "文件内容...", success=True)
recorder.end_step()

# 4. 结束录制
trace = recorder.end_trace()

# 5. 分析轨迹
analyzer = TraceAnalyzer(trace)
result = analyzer.analyze()

print(f"总耗时: {result.total_duration_ms}ms")
print(f"总Token: {result.total_tokens}")
print(f"成功率: {result.success_rate:.1%}")
```

### CLI 使用

```bash
# 分析轨迹文件
agentreplay analyze trace.json

# 导出为 HTML 报告
agentreplay export trace.json --format html --output report.html

# 回放轨迹
agentreplay replay trace.json --speed 2.0

# 创建演示轨迹
agentreplay demo --output demo_trace.json
```

## 📖 详细使用指南

### 录制执行轨迹

```python
from agentreplay import TraceRecorder, EventType, AgentFramework

recorder = TraceRecorder(
    agent_name="ClaudeCode",
    framework=AgentFramework.CLAUDE_CODE,
    output_dir="./traces",  # 自动保存目录
    auto_save=True          # 自动保存
)

# 开始录制
trace_id = recorder.start_trace(
    task="优化 Python 代码性能",
    metadata={"version": "1.0", "user": "demo"}
)

# 记录思考过程
recorder.record_thinking("让我分析一下这段代码...", tokens_used=20)

# 记录工具调用
recorder.record_tool_call("Read", {"file_path": "app.py"}, duration_ms=45)

# 记录决策
recorder.record_decision("使用缓存优化", "频繁调用的函数应该缓存结果")

# 记录检查点
recorder.record_checkpoint("analysis_complete", {"issues_found": 3})

# 记录错误
recorder.record_error("文件不存在", error_type="FileNotFoundError")

# 结束录制
trace = recorder.end_trace()
```

### 回放执行轨迹

```python
from agentreplay import Trace, TracePlayer

# 加载轨迹
trace = Trace.load("trace.json")

# 创建播放器
player = TracePlayer(trace)

# 设置回调
def on_event(event):
    print(f"[{event.event_type.value}] {event.content[:50]}...")

player.set_callbacks(on_event=on_event)

# 播放轨迹
for event in player.play(speed=2.0):  # 2倍速
    pass

# 逐步调试
event = player.step_forward()  # 前进一步
event = player.step_backward()  # 后退一步

# 获取进度
progress = player.get_progress()
print(f"进度: {progress['progress_percent']:.1f}%")
```

### 分析执行轨迹

```python
from agentreplay import Trace, TraceAnalyzer

trace = Trace.load("trace.json")
analyzer = TraceAnalyzer(trace)

# 执行分析
result = analyzer.analyze()

# 查看统计信息
print(f"总耗时: {result.total_duration_ms}ms")
print(f"平均步骤耗时: {result.avg_step_duration_ms}ms")
print(f"总Token: {result.total_tokens}")
print(f"成功率: {result.success_rate:.1%}")

# 查看工具使用统计
for tool_name, stats in result.tool_stats.items():
    print(f"{tool_name}: {stats.call_count}次调用")

# 查看瓶颈
for bottleneck in result.bottlenecks:
    print(f"瓶颈: {bottleneck['message']}")

# 查看建议
for rec in result.recommendations:
    print(f"建议: {rec}")
```

### 导出分析报告

```python
from agentreplay import Trace, TraceAnalyzer
from agentreplay.exporters import export_trace

trace = Trace.load("trace.json")
analyzer = TraceAnalyzer(trace)
result = analyzer.analyze()

# 导出为 JSON
export_trace(trace, result, format="json", output_path="report.json")

# 导出为 Markdown
export_trace(trace, result, format="markdown", output_path="report.md")

# 导出为 HTML（带可视化）
export_trace(trace, result, format="html", output_path="report.html")

# 导出为 CSV
export_trace(trace, result, format="csv", output_path="report.csv")
```

## 💡 设计思路与迭代规划

### 设计理念

AgentReplay 的设计灵感来源于对 AI Agent 调试的痛点观察：

1. **黑盒问题**：AI Agent 的决策过程难以追踪
2. **复现困难**：执行失败后难以复现问题
3. **优化无据**：缺乏数据支撑的优化方向

### 技术选型

- **纯 Python 实现**：零依赖，降低使用门槛
- **JSON 存储**：通用格式，便于集成和扩展
- **模块化设计**：录制、回放、分析、导出独立解耦

### 后续迭代计划

- [ ] 添加 TUI 可视化界面
- [ ] 支持实时流式录制
- [ ] 添加轨迹压缩算法
- [ ] 支持分布式轨迹存储
- [ ] 集成更多 Agent 框架格式

## 📦 打包与部署指南

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/gitstq/AgentReplay.git
cd AgentReplay

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 运行演示
python examples/demo.py
```

### 构建发布

```bash
# 构建
python -m build

# 发布到 PyPI
twine upload dist/*
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 开源协议

本项目采用 MIT 协议开源 - 详见 [LICENSE](LICENSE) 文件

---

<a name="繁體中文"></a>
# 🎬 AgentReplay

**輕量級 AI Agent 執行軌跡回放與分析引擎**

## 🎉 專案介紹

AgentReplay 是一個專為 AI Agent 開發者設計的執行軌跡錄製、回放與分析工具。它可以幫助你：

- 🔍 **完整記錄** AI Agent 的決策過程、工具調用、Token 消耗
- 📼 **靈活回放** 支援逐步/快速回放，精準定位問題節點
- 📊 **智能分析** 自動分析執行效率、決策品質、資源消耗
- 🔄 **差異對比** 對比不同執行軌跡，發現優化空間

**自研差異化亮點**：
- ✅ 零依賴純 Python 實現，開箱即用
- ✅ 支援 Claude Code、Cursor、Codex、Windsurf 等多框架格式
- ✅ 多格式報告匯出（JSON/Markdown/HTML/CSV）
- ✅ 輕量級設計，單檔案即可執行

## ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🎥 **軌跡錄製** | 即時記錄 Agent 執行過程，支援思考、工具調用、決策、錯誤等事件類型 |
| 📼 **軌跡回放** | 支援即時/快速/逐步回放模式，可設置斷點除錯 |
| 📊 **智能分析** | 自動統計耗時、Token 消耗、成功率、工具使用頻率等指標 |
| 🔧 **多框架支援** | 相容 Claude Code、Cursor、Codex、Windsurf、Copilot 等主流框架 |
| 📤 **多格式匯出** | 支援 JSON、Markdown、HTML、CSV 等格式匯出分析報告 |
| 🎯 **零依賴** | 純 Python 實現，無需安裝任何第三方依賴 |

## 🚀 快速開始

### 環境要求

- Python 3.8+
- 無需額外依賴

### 安裝

```bash
# 從 PyPI 安裝（推薦）
pip install agentreplay

# 或從原始碼安裝
git clone https://github.com/gitstq/AgentReplay.git
cd AgentReplay
pip install -e .
```

### 基本使用

```python
from agentreplay import TraceRecorder, TraceAnalyzer, AgentFramework

# 1. 建立錄製器
recorder = TraceRecorder(
    agent_name="MyAgent",
    framework=AgentFramework.CLAUDE_CODE
)

# 2. 開始錄製
recorder.start_trace("分析程式碼並提供建議")

# 3. 記錄執行過程
recorder.start_step("讀取檔案")
recorder.record_thinking("需要先讀取檔案內容...", tokens_used=15)
recorder.record_tool_call("Read", {"file_path": "main.py"}, duration_ms=50)
recorder.record_tool_result("Read", "檔案內容...", success=True)
recorder.end_step()

# 4. 結束錄製
trace = recorder.end_trace()

# 5. 分析軌跡
analyzer = TraceAnalyzer(trace)
result = analyzer.analyze()

print(f"總耗時: {result.total_duration_ms}ms")
print(f"總Token: {result.total_tokens}")
print(f"成功率: {result.success_rate:.1%}")
```

### CLI 使用

```bash
# 分析軌跡檔案
agentreplay analyze trace.json

# 匯出為 HTML 報告
agentreplay export trace.json --format html --output report.html

# 回放軌跡
agentreplay replay trace.json --speed 2.0

# 建立示範軌跡
agentreplay demo --output demo_trace.json
```

## 📄 開源協議

本專案採用 MIT 協議開源 - 詳見 [LICENSE](LICENSE) 檔案

---

<a name="english"></a>
# 🎬 AgentReplay

**Lightweight AI Agent Execution Trace Replay & Analysis Engine**

## 🎉 Introduction

AgentReplay is an execution trace recording, replay, and analysis tool designed for AI Agent developers. It helps you:

- 🔍 **Complete Recording** of AI Agent decision processes, tool calls, and token consumption
- 📼 **Flexible Replay** with step-by-step/fast playback to precisely locate problem nodes
- 📊 **Intelligent Analysis** of execution efficiency, decision quality, and resource consumption
- 🔄 **Diff Comparison** between different execution traces to discover optimization opportunities

**Self-developed Highlights**:
- ✅ Zero-dependency pure Python implementation, ready to use
- ✅ Support for Claude Code, Cursor, Codex, Windsurf and other frameworks
- ✅ Multi-format report export (JSON/Markdown/HTML/CSV)
- ✅ Lightweight design, runs from a single file

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🎥 **Trace Recording** | Real-time recording of Agent execution, supporting thinking, tool calls, decisions, errors, etc. |
| 📼 **Trace Replay** | Support for real-time/fast/step-by-step playback modes with breakpoint debugging |
| 📊 **Intelligent Analysis** | Automatic statistics on duration, token usage, success rate, tool frequency, etc. |
| 🔧 **Multi-framework Support** | Compatible with Claude Code, Cursor, Codex, Windsurf, Copilot, etc. |
| 📤 **Multi-format Export** | Support for JSON, Markdown, HTML, CSV format analysis reports |
| 🎯 **Zero Dependencies** | Pure Python implementation, no third-party dependencies required |

## 🚀 Quick Start

### Requirements

- Python 3.8+
- No additional dependencies

### Installation

```bash
# Install from PyPI (recommended)
pip install agentreplay

# Or install from source
git clone https://github.com/gitstq/AgentReplay.git
cd AgentReplay
pip install -e .
```

### Basic Usage

```python
from agentreplay import TraceRecorder, TraceAnalyzer, AgentFramework

# 1. Create recorder
recorder = TraceRecorder(
    agent_name="MyAgent",
    framework=AgentFramework.CLAUDE_CODE
)

# 2. Start recording
recorder.start_trace("Analyze code and provide suggestions")

# 3. Record execution
recorder.start_step("Read file")
recorder.record_thinking("Need to read file content first...", tokens_used=15)
recorder.record_tool_call("Read", {"file_path": "main.py"}, duration_ms=50)
recorder.record_tool_result("Read", "File content...", success=True)
recorder.end_step()

# 4. End recording
trace = recorder.end_trace()

# 5. Analyze trace
analyzer = TraceAnalyzer(trace)
result = analyzer.analyze()

print(f"Total duration: {result.total_duration_ms}ms")
print(f"Total tokens: {result.total_tokens}")
print(f"Success rate: {result.success_rate:.1%}")
```

### CLI Usage

```bash
# Analyze trace file
agentreplay analyze trace.json

# Export to HTML report
agentreplay export trace.json --format html --output report.html

# Replay trace
agentreplay replay trace.json --speed 2.0

# Create demo trace
agentreplay demo --output demo_trace.json
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
