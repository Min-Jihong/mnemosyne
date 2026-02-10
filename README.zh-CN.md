<div align="center">

# 🧠 Mnemosyne

### *创造另一个你*

**学习像你一样思考的数字克隆**

中文 | [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

[![CI](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos)

</div>

---

## 🪞 数字自我的梦想

> *每个人都曾梦想过创造"另一个自己"。*

一个在你睡觉时工作的你。一个在你疲惫时思考的你。一个了解你的习惯、理解你的偏好、像你一样做决定的存在。

**Mnemosyne**是让这个梦想成真的项目。

它记录你在电脑前的每一个动作 — 鼠标点击、键盘输入、应用切换、滚动 — 同时AI不断询问**"为什么做这个动作？"**并学习。它不仅仅模仿行为，而是**学习你的思维方式本身**。

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│     "为什么点击那里？"                                              │
│     "切换应用时在想什么？"                                          │
│     "我注意到你总是在X之前做Y。为什么？"                            │
│                                                                    │
│                    — Mnemosyne，正在学习成为你                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Mnemosyne的不同之处

| 传统自动化工具 | Mnemosyne |
|--------------|-----------|
| 记录**做了什么** | 理解**为什么做** |
| 重放固定脚本 | 适应新情况 |
| 会话间无记忆 | 永远记住一切 |
| 被动工具 | 主动好奇的AI |

---

## 🎯 主要功能

### 📹 微动作记录
以毫秒级精度捕获每一个交互：
- **鼠标**：位置、点击、双击、拖动、滚动、悬停时间
- **键盘**：按键、快捷键、打字速度和模式
- **屏幕**：重要操作时自动截图
- **上下文**：活动应用、窗口标题、URL、文件路径

### 🤔 好奇的LLM
与被动记录工具不同，Mnemosyne的AI**真正具有好奇心**：

```python
# AI不只是观看 — 它提问
curiosities = await curious_llm.observe_and_wonder(events)

# 示例输出：
# "为什么今天从VS Code切换到Chrome 47次？"
# "写完后总是向上滚动。是在重读吗？"
# "每次'git commit'前都会停顿3秒。是在犹豫吗？"
```

### 🧠 持久记忆
永不遗忘的记忆系统：
- **语义搜索**：通过含义而非关键词查找记忆
- **记忆整合**：从模式中自动生成洞察
- **向量存储**：使用ChromaDB实现快速检索
- **长期学习**：建立数周、数月的理解

### 🤖 执行代理
你的数字孪生可以执行操作：
- 目标导向的计算机控制
- 安全防护（速率限制、阻止的应用、紧急停止）
- 谨慎执行的确认模式
- 从你的修正中学习

### 🔌 多提供商LLM支持
使用你信任的AI提供商：
- **OpenAI**：GPT-4、GPT-4 Turbo
- **Anthropic**：Claude 3、Claude 3.5
- **Google**：Gemini Pro、Gemini Ultra
- **Ollama**：本地运行Llama、Mistral等

### 🌐 Web界面
随时随地与你的数字孪生聊天：
- **现代聊天UI**进行自然语言交互
- 在浏览器中**配置API密钥**
- **录制控制**仪表板
- **记忆搜索**界面

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/mnemosyne.git
cd mnemosyne

# 使用pip安装
pip install -e .

# Web界面
pip install -e ".[web]"

# TUI
pip install -e ".[tui]"

# macOS原生捕获（推荐）
pip install -e ".[macos]"

# 所有功能
pip install -e ".[all]"
```

### 授予权限（macOS）

Mnemosyne需要以下权限：

| 权限 | 位置 | 原因 |
|------|------|------|
| **辅助功能** | 系统设置 → 隐私 → 辅助功能 | 鼠标/键盘捕获 |
| **输入监控** | 系统设置 → 隐私 → 输入监控 | 键盘事件 |
| **屏幕录制** | 系统设置 → 隐私 → 屏幕录制 | 截图 |

### 设置

```bash
mnemosyne setup
```

---

## 📖 使用方法

### Web界面（推荐）

```bash
# 启动Web UI
mnemosyne web

# 在浏览器中打开 http://localhost:8000
```

### TUI（终端UI）

```bash
# 启动Textual TUI
mnemosyne tui
```

### 命令行

```bash
# 开始录制
mnemosyne record --name "工作会话"

# 分析会话
mnemosyne analyze abc123

# 搜索记忆
mnemosyne memory "早晨例行工作"

# 执行目标
mnemosyne execute "设置开发环境"
```

---

## 🎮 CLI参考

| 命令 | 描述 |
|------|------|
| `mnemosyne setup` | 交互式配置向导 |
| `mnemosyne web` | 启动Web界面 |
| `mnemosyne tui` | 启动终端UI |
| `mnemosyne record` | 开始录制活动 |
| `mnemosyne sessions` | 列出录制会话 |
| `mnemosyne analyze <id>` | AI分析会话 |
| `mnemosyne memory [query]` | 搜索或浏览记忆 |
| `mnemosyne execute <goal>` | 执行目标 |
| `mnemosyne status` | 显示配置状态 |

---

## 🤝 贡献

欢迎贡献！提交PR前请阅读贡献指南。

---

## 📄 许可证

MIT License - 详见[LICENSE](LICENSE)。

---

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw) - 计算机控制概念
- [OpenAdapt](https://github.com/OpenAdaptAI/OpenAdapt) - 录制模式
- [pynput](https://github.com/moses-palmer/pynput) - 输入监控
