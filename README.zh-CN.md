<div align="center">

# 🧠 Mnemosyne

### *创造另一个你*

**学习像你一样思考的数字克隆**

中文 | [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

[![CI](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

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

<div align="center">

## ⭐ 为什么给这个项目加星？

</div>

<table>
<tr>
<td width="50%">

### 🎯 **不只是记录 — 而是理解**
当其他工具只捕获像素时，Mnemosyne捕获的是**意图**。AI在每个动作后都会问"为什么？"，构建你思维方式的模型。

### 🔍 **用OCR搜索你的过去**
找到上周看到的那个东西。OCR索引每张截图，让你可以按文本内容搜索。

</td>
<td width="50%">

### 📊 **更好地了解自己**
AI生成的每日总结和生产力统计揭示你从未注意到的行为模式。

### ⏪ **时间旅行你的操作**
回放任何会话，精确查看你做了什么、什么时候做的，以及（感谢AI）*为什么*这样做。

</td>
</tr>
</table>

<div align="center">

**唯一一个不只是观察你 — 而是*学习成为你*的工具。**

</div>

---

## 🎬 实际演示

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MNEMOSYNE 工作流程                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   你                           MNEMOSYNE                        输出        │
│    │                              │                               │         │
│    │  ┌─────────────────┐        │                               │         │
│    ├──│ 点击、输入、    │───────►│  📹 捕获                      │         │
│    │  │ 滚动、切换      │        │  每一个微动作                  │         │
│    │  └─────────────────┘        │         │                     │         │
│    │                             │         ▼                     │         │
│    │                             │  🤔 推理                      │         │
│    │  ┌─────────────────┐        │  "为什么这样做？"              │         │
│    │◄─│ AI向你提问      │◄───────│         │                     │         │
│    │  │ 好奇的问题      │        │         ▼                     │         │
│    │  └─────────────────┘        │  🧠 记忆                      │         │
│    │                             │  模式 → 记忆                   │         │
│    │                             │         │                     │         │
│    │                             │         ▼                     │         │
│    │                             │  ┌─────────────────────────┐  │         │
│    │                             │  │ 📊 每日总结             │──┼────►    │
│    │                             │  │ 🔍 OCR搜索              │  │         │
│    │                             │  │ ⏪ 动作回放             │  │         │
│    │                             │  │ 🤖 执行目标             │  │         │
│    │                             │  └─────────────────────────┘  │         │
│    │                                                             │         │
└────┴─────────────────────────────────────────────────────────────┴─────────┘

$ mnemosyne summary today
┌──────────────────────────────────────────────────────────────────┐
│  📊 今日概览                                    2026年2月11日     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ⏱️  活跃时间: 6小时42分                                          │
│  🖱️  点击: 2,847  |  ⌨️  按键: 18,392                             │
│  🔄  应用切换: 234  |  📸 截图: 89                                 │
│                                                                  │
│  🏆 常用应用                    🧠 AI洞察                         │
│  ├─ VS Code      3小时12分     "你在周二的上下文切换较少。        │
│  ├─ Chrome       1小时45分      考虑在中午前屏蔽Slack？"          │
│  ├─ Slack          38分                                          │
│  └─ Terminal       27分                                          │
│                                                                  │
│  💡 "你输入了47次'git status'但只提交了5次。                     │
│      这是9:1的检查提交比。是焦虑还是流程问题？"                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
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

## 🏆 竞品对比

| 功能 | Mnemosyne | Screenpipe | OpenAdapt | Rewind |
|------|:---------:|:----------:|:---------:|:------:|
| **微动作捕获** | ✅ | ❌ | ✅ | ❌ |
| **意图推理（为什么？）** | ✅ | ❌ | ❌ | ❌ |
| **好奇AI提问** | ✅ | ❌ | ❌ | ❌ |
| **OCR文本搜索** | ✅ | ✅ | ❌ | ✅ |
| **AI每日总结** | ✅ | ❌ | ❌ | ❌ |
| **动作回放** | ✅ | ❌ | ✅ | ❌ |
| **语义记忆** | ✅ | ❌ | ❌ | ❌ |
| **目标执行** | ✅ | ❌ | ✅ | ❌ |
| **多LLM支持** | ✅ | ❌ | ✅ | ❌ |
| **本地优先/隐私** | ✅ | ✅ | ✅ | ❌ |
| **隐私保护（PII）** | ✅ | ❌ | ✅ | ❌ |
| **视觉定位（Set-of-Mark）** | ✅ | ❌ | ✅ | ❌ |
| **事件聚合** | ✅ | ❌ | ✅ | ❌ |
| **开源** | ✅ | ✅ | ✅ | ❌ |

**Screenpipe** = 音视频为主 | **OpenAdapt** = 视觉定位RPA | **Rewind** = OCR搜索（闭源）

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

### 📊 分析与洞察
**新功能！** 前所未有地了解你的工作模式：

```bash
# 获取AI生成的每日总结
$ mnemosyne summary today

📊 每日总结 - 2026年2月11日
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 主要焦点：后端API开发
   你在VS Code中花费了68%的活跃时间处理认证模块。

💡 关键洞察：你最高效的时间是上午9-11点。
   考虑在这个时间段安排深度工作。

⚠️  模式警告：午餐后30分钟内有12次上下文切换。
   这与较低的代码产出相关。

# 获取详细的生产力统计
$ mnemosyne stats week

📈 周统计
├─ 总活跃时间：34小时12分
├─ 最常用应用：VS Code（18小时45分）
├─ 高峰生产力：周二 9:00-11:30am
├─ 平均会话时长：47分钟
└─ 专注分数：7.2/10（比上周↑ 0.8）
```

### 🔍 OCR搜索
**新功能！** 找到你在屏幕上看到过的任何内容：

```bash
# 在所有截图中搜索文本
$ mnemosyne search "API_KEY"

🔍 找到3个匹配：

1. [2月10日, 14:32] VS Code - .env文件
   "OPENAI_API_KEY=sk-..."
   
2. [2月9日, 11:15] Chrome - OpenAI仪表板
   "你的API_KEY已轮换"
   
3. [2月8日, 16:45] Slack - #dev频道
   "谁能分享一下staging的API_KEY？"
```

### ⏪ 动作回放
**新功能！** 穿越时间回顾你的会话：

```bash
# 回放录制的会话
$ mnemosyne replay ses_abc123

⏪ 回放会话："早晨编码"（2026年2月10日）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[09:00:15] 🖱️  点击：Dock中的VS Code图标
[09:00:16] ⌨️  快捷键：Cmd+Shift+P（命令面板）
[09:00:18] ⌨️  输入："git pull"
[09:00:19] 🖱️  点击：终端面板
           💭 意图："开始工作前同步最新更改"
[09:00:25] ⌨️  快捷键：Cmd+P（快速打开）
[09:00:27] ⌨️  输入："auth.py"
           💭 意图："继续处理认证模块"

控制：[空格] 暂停 | [←/→] 步进 | [Q] 退出 | [S] 速度
```

### 🔒 隐私保护
**新功能！** 自动检测和遮蔽个人身份信息（PII）：

```bash
# 检查隐私设置
$ mnemosyne privacy status

🔒 隐私保护：已启用
   级别：standard
   PII类型：email, phone, ssn, credit_card, api_key, password

# 测试PII检测
$ mnemosyne privacy test "联系 john@email.com 或拨打 555-123-4567"

🔍 检测到PII：
   [EMAIL] john@email.com → [EMAIL_REDACTED]
   [PHONE] 555-123-4567 → [PHONE_REDACTED]

# 清洗文件
$ mnemosyne privacy scrub-file ./notes.txt
✅ 清洗了3个PII实例 → ./notes.scrubbed.txt
```

**支持的PII类型：**
- 📧 电子邮件地址
- 📞 电话号码
- 🆔 身份证号/社会安全号
- 💳 信用卡号
- 🔑 API密钥和密钥
- 🔐 密码（在URL、配置中）
- 🌐 IP和MAC地址

### 🎯 视觉定位（Set-of-Mark）
**新功能！** AI驱动的UI元素检测，用于计算机控制：

```bash
# 检测截图中的UI元素
$ mnemosyne ground screenshot.png --prompt

🎯 检测到UI元素：12个

[1] BUTTON @ (145, 230) - "提交"
[2] INPUT @ (120, 180) - 文本框
[3] LINK @ (50, 320) - "了解更多"
[4] BUTTON @ (290, 230) - "取消"
...

📝 生成的Set-of-Mark提示：
"截图显示一个表单，包含以下交互元素：
 [1] 右上角的提交按钮
 [2] 邮箱文本输入框
 [3] 底部的'了解更多'链接
 [4] 提交按钮旁边的取消按钮
 
 要提交表单，点击元素[1]。"
```

### 📦 事件聚合
**新功能！** 通过合并重复事件减少噪音：

```bash
# 聚合会话中的事件
$ mnemosyne aggregate ses_abc123

📦 聚合结果：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   原始事件：15,847
   聚合后：  1,234
   压缩率：  92.2%

   🖱️  鼠标移动：12,456 → 89条轨迹
   📜 滚动事件：1,203 → 45个滚动动作
   ⌨️  按键：    2,188 → 156个输入段
   
   💾 节省存储：14.2 MB → 1.1 MB
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

# macOS原生捕获（推荐）
pip install -e ".[macos]"

# ML训练功能
pip install -e ".[ml]"

# 所有功能
pip install -e ".[all]"
```

### 授予权限（macOS）

Mnemosyne需要以下权限来观察你的行为：

| 权限 | 位置 | 原因 |
|------|------|------|
| **辅助功能** | 系统设置 → 隐私 → 辅助功能 | 鼠标/键盘捕获 |
| **输入监控** | 系统设置 → 隐私 → 输入监控 | 键盘事件 |
| **屏幕录制** | 系统设置 → 隐私 → 屏幕录制 | 截图 |

### 设置

```bash
mnemosyne setup
```

这个交互式向导配置：
- 🔑 LLM提供商和API密钥
- 🤖 模型选择
- 🧠 好奇模式（被动/主动/积极）

---

## 📖 使用方法

### Web界面（推荐）

```bash
# 启动Web UI
mnemosyne web

# 在浏览器中打开 http://localhost:8000
```

Web界面让你可以：
- 与你的数字孪生聊天
- 使用API密钥配置LLM设置
- 开始/停止录制会话
- 搜索你的记忆

### 命令行

#### 开始录制

```bash
# 开始录制会话
mnemosyne record --name "我的工作日"

# 录制中... 每个动作都在被捕获。
# 按Ctrl+C停止。
```

#### AI分析

```bash
# 分析会话 - AI推断每个动作的意图
mnemosyne analyze abc123

# 让好奇的AI询问关于你行为的问题
mnemosyne curious abc123
```

**好奇输出示例：**
```
🤔 关于你会话的问题：

1. [高] 为什么你总是在查看邮件前先打开Slack？
   类别：工作流程 | 置信度：0.89

2. [中] 你输入了23次"git status"但只提交了3次。为什么？
   类别：习惯 | 置信度：0.72

3. [高] 切换到终端前有一个持续2秒的停顿。
   类别：决策 | 置信度：0.85
```

#### 记忆操作

```bash
# 语义搜索记忆
mnemosyne memory "我通常怎么开始早晨的工作"

# 浏览最近的记忆
mnemosyne memory --recent

# 查找重要洞察
mnemosyne memory --important
```

#### 执行目标

```bash
# 基于学习的行为执行目标
mnemosyne execute "设置我常用的编码环境"

# 使用确认模式（更安全）
mnemosyne execute "回复待处理的消息" --confirm
```

---

## 🎮 CLI参考

| 命令 | 描述 |
|------|------|
| `mnemosyne setup` | 交互式配置向导 |
| `mnemosyne web` | **启动Web界面** |
| `mnemosyne record` | 开始录制活动 |
| `mnemosyne sessions` | 列出所有录制会话 |
| `mnemosyne analyze <id>` | AI分析会话意图 |
| `mnemosyne curious <id>` | AI询问关于行为的问题 |
| `mnemosyne memory [query]` | 搜索或浏览记忆 |
| `mnemosyne export <id>` | 导出会话用于训练 |
| `mnemosyne execute <goal>` | 执行目标 |
| `mnemosyne status` | 显示当前配置 |
| `mnemosyne version` | 显示版本 |
| | |
| **📊 分析** | |
| `mnemosyne summary [today\|yesterday\|week]` | AI生成的每日/每周总结 |
| `mnemosyne stats [today\|yesterday\|week]` | 工作统计和生产力指标 |
| | |
| **🔍 搜索与回放** | |
| `mnemosyne search <query>` | 跨截图的OCR文本搜索 |
| `mnemosyne replay <session_id>` | 回放带意图的录制动作 |
| | |
| **🔒 隐私与处理** | |
| `mnemosyne privacy status` | 显示隐私保护设置 |
| `mnemosyne privacy enable/disable` | 切换PII清洗 |
| `mnemosyne privacy level [aggressive\|standard\|minimal]` | 设置清洗级别 |
| `mnemosyne privacy test <text>` | 测试PII检测 |
| `mnemosyne ground <image>` | 检测UI元素（Set-of-Mark） |
| `mnemosyne aggregate <session_id>` | 压缩重复事件 |

---

## ⚙️ 配置

配置存储在 `~/.mnemosyne/config.toml`：

```toml
[llm]
provider = "anthropic"  # openai, anthropic, google, ollama
model = "claude-3-opus-20240229"
api_key = "your-api-key"

[curiosity]
mode = "active"  # passive, active, proactive

[recording]
screenshot_quality = 80
screenshot_format = "webp"
mouse_throttle_ms = 50
```

---

## 🏗️ 项目结构

```
mnemosyne/
├── capture/      # 输入录制（鼠标、键盘、屏幕）
├── store/        # SQLite数据库和会话管理
├── reason/       # LLM推理和好奇提问
├── memory/       # 带向量搜索的持久记忆
├── learn/        # 训练流水线和数据集
├── execute/      # 计算机控制代理
├── llm/          # 多提供商LLM抽象
├── analytics/    # 总结生成和统计
├── ocr/          # 截图文本提取和搜索
├── replay/       # 会话回放引擎
├── privacy/      # PII检测和清洗
├── grounding/    # 视觉UI元素检测（Set-of-Mark）
├── aggregation/  # 事件压缩和路径简化
├── config/       # 设置和配置
├── cli/          # 命令行界面
└── web/          # Web界面（FastAPI + HTML/JS）
```

---

## 🔄 工作原理

### 1. 捕获阶段
记录你执行的每一个微动作：
- 鼠标位置、点击、滚动
- 键盘输入和快捷键
- 关键时刻的截图
- 活动窗口上下文

### 2. 推理阶段
好奇的LLM分析你的动作：
- **"为什么点击那里？"**
- **"你的输入有什么模式？"**
- **"为什么从应用A切换到应用B？"**

### 3. 学习阶段
提取并学习模式：
- 动作序列变成习惯
- 意图变得可预测
- 你的"数字孪生"逐渐形成

### 4. 执行阶段
学习的模型可以行动：
- 基于过去行为执行目标
- 安全防护阻止危险操作
- 敏感操作需要确认

---

## 🛡️ 安全功能

Mnemosyne包含多重安全机制：

- **速率限制**：默认每分钟最多60个动作
- **阻止的应用**：终端、密码管理器、系统偏好设置
- **阻止的快捷键**：Cmd+Q、Cmd+Shift+Q等
- **安全区域**：将动作限制在特定屏幕区域
- **紧急停止**：立即停止所有动作

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

---

<div align="center">

**如果Mnemosyne帮助你更好地了解自己，请考虑给它一个 ⭐**

*由想要更好了解自己的人类带着好奇心构建。*

</div>
