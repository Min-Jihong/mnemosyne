<div align="center">

# 🧠 Mnemosyne

### *Create Another You*

**Your Digital Clone That Learns How You Think**

[한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh-CN.md) | English

[![CI](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</div>

---

## 🪞 The Dream of Digital Self

> *Everyone has dreamed of creating another "me" at least once.*

Another you that works while you sleep. Another you that thinks when you're tired. Another being that knows your habits, understands your preferences, and makes decisions like you would.

**Mnemosyne** is the project that makes this dream reality.

It records every action you take at your computer — mouse clicks, keyboard inputs, app switches, scrolls — while AI continuously asks **"Why did you do this?"** and learns. It doesn't just mimic your actions. **It learns your thought patterns themselves.**

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│     "Why did you click there?"                                     │
│     "What were you thinking when you switched apps?"               │
│     "I noticed you always do X before Y. Why?"                     │
│                                                                    │
│                    — Mnemosyne, learning to be you                 │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## ✨ What Makes Mnemosyne Different

| Traditional Automation | Mnemosyne |
|------------------------|-----------|
| Records **what** you do | Understands **why** you do it |
| Replays fixed scripts | Adapts to new situations |
| No memory between sessions | Remembers everything forever |
| Passive tool | Actively curious AI |

---

## 🎯 Features

### 📹 Micro-Action Recording
Every tiny interaction is captured with millisecond precision:
- **Mouse**: Position, clicks, double-clicks, drag, scroll, hover time
- **Keyboard**: Key presses, hotkeys, typing speed and patterns
- **Screen**: Automatic screenshots on significant actions
- **Context**: Active app, window title, URL, file path

### 🤔 Curious LLM (Not Just Analysis)
Unlike passive recording tools, Mnemosyne's AI is **genuinely curious**:

```python
# The AI doesn't just watch — it asks questions
curiosities = await curious_llm.observe_and_wonder(events)

# Example output:
# "Why did you switch from VS Code to Chrome 47 times today?"
# "You always scroll up after writing. Are you re-reading?"
# "There's a 3-second pause before every 'git commit'. Hesitation?"
```

### 🧠 Persistent Memory
OpenClaw-inspired memory system that never forgets:
- **Semantic search**: Find memories by meaning, not keywords
- **Memory consolidation**: Auto-generates insights from patterns
- **Vector store**: ChromaDB for lightning-fast retrieval
- **Long-term learning**: Builds understanding over weeks and months

### 🤖 Execution Agent
Your digital twin can take action:
- Goal-oriented computer control
- Safety guards (rate limiting, blocked apps, emergency stop)
- Confirmation mode for careful execution
- Learns from your corrections

### 🔌 Multi-Provider LLM Support
Use the AI provider you trust:
- **OpenAI**: GPT-4, GPT-4 Turbo
- **Anthropic**: Claude 3, Claude 3.5
- **Google**: Gemini Pro, Gemini Ultra
- **Ollama**: Run locally with Llama, Mistral, etc.

### 🌐 Web Interface
Chat with your digital twin from anywhere:
- **Modern chat UI** for natural language interaction
- **API key configuration** in the browser
- **Recording control** dashboard
- **Memory search** interface

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mnemosyne.git
cd mnemosyne

# Install with pip
pip install -e .

# For web interface
pip install -e ".[web]"

# For macOS native capture (recommended)
pip install -e ".[macos]"

# For ML training capabilities
pip install -e ".[ml]"

# All features
pip install -e ".[all]"
```

### Grant Permissions (macOS)

Mnemosyne needs these permissions to observe your behavior:

| Permission | Location | Why |
|------------|----------|-----|
| **Accessibility** | System Settings → Privacy → Accessibility | Mouse/keyboard capture |
| **Input Monitoring** | System Settings → Privacy → Input Monitoring | Keyboard events |
| **Screen Recording** | System Settings → Privacy → Screen Recording | Screenshots |

### Setup

```bash
mnemosyne setup
```

This interactive wizard configures:
- 🔑 LLM provider and API key
- 🤖 Model selection
- 🧠 Curiosity mode (passive/active/proactive)

---

## 📖 Usage

### Web Interface (Recommended)

```bash
# Start the web UI
mnemosyne web

# Open http://localhost:8000 in your browser
```

The web interface lets you:
- Chat with your digital twin
- Configure LLM settings with your API key
- Start/stop recording sessions
- Search your memories

### Command Line

#### Start Recording

```bash
# Start a recording session
mnemosyne record --name "My Work Day"

# Recording... Every action is being captured.
# Press Ctrl+C to stop.
```

#### Analyze with AI

```bash
# Analyze a session - AI infers intent for each action
mnemosyne analyze abc123

# Let the curious AI ask questions about your behavior
mnemosyne curious abc123
```

**Example Curiosity Output:**
```
🤔 Questions about your session:

1. [HIGH] Why do you always open Slack before checking email?
   Category: workflow | Confidence: 0.89

2. [MEDIUM] You typed "git status" 23 times but only committed 3 times. Why?
   Category: habit | Confidence: 0.72

3. [HIGH] There's a consistent 2-second pause before switching to Terminal.
   Category: decision | Confidence: 0.85
```

#### Memory Operations

```bash
# Search memories semantically
mnemosyne memory "how do I usually start my morning"

# Browse recent memories
mnemosyne memory --recent

# Find important insights
mnemosyne memory --important
```

#### Execute Goals

```bash
# Execute a goal based on learned behavior
mnemosyne execute "Set up my usual coding environment"

# With confirmation mode (safer)
mnemosyne execute "Reply to pending messages" --confirm
```

---

## 🎮 CLI Reference

| Command | Description |
|---------|-------------|
| `mnemosyne setup` | Interactive configuration wizard |
| `mnemosyne web` | **Start web interface** |
| `mnemosyne record` | Start recording your activity |
| `mnemosyne sessions` | List all recorded sessions |
| `mnemosyne analyze <id>` | AI analyzes session intent |
| `mnemosyne curious <id>` | AI asks questions about behavior |
| `mnemosyne memory [query]` | Search or browse memories |
| `mnemosyne export <id>` | Export session for training |
| `mnemosyne execute <goal>` | Execute a goal |
| `mnemosyne status` | Show current configuration |
| `mnemosyne version` | Show version |

---

## ⚙️ Configuration

Configuration is stored in `~/.mnemosyne/config.toml`:

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

## 🏗️ Project Structure

```
mnemosyne/
├── capture/      # Input recording (mouse, keyboard, screen)
├── store/        # SQLite database and session management
├── reason/       # LLM inference and curious questioning
├── memory/       # Persistent memory with vector search
├── learn/        # Training pipeline and dataset
├── execute/      # Computer control agent
├── llm/          # Multi-provider LLM abstraction
├── config/       # Settings and configuration
├── cli/          # Command-line interface
└── web/          # Web interface (FastAPI + HTML/JS)
```

---

## 🔄 How It Works

### 1. Capture Phase
Every micro-action you perform is recorded:
- Mouse position, clicks, scrolls
- Keyboard inputs and hotkeys
- Screenshots at key moments
- Active window context

### 2. Reason Phase
The curious LLM analyzes your actions:
- **"Why did you click there?"**
- **"What pattern exists in your typing?"**
- **"Why switch from App A to App B?"**

### 3. Learn Phase
Patterns are extracted and learned:
- Action sequences become habits
- Intent becomes predictable
- Your "digital twin" emerges

### 4. Execute Phase
The learned model can act:
- Execute goals based on past behavior
- Safe guards prevent dangerous actions
- Confirmation for sensitive operations

---

## 🛡️ Safety Features

Mnemosyne includes multiple safety mechanisms:

- **Rate limiting**: Max 60 actions/minute by default
- **Blocked apps**: Terminal, Password managers, System Preferences
- **Blocked hotkeys**: Cmd+Q, Cmd+Shift+Q, etc.
- **Safe zones**: Restrict actions to specific screen areas
- **Emergency stop**: Immediate halt of all actions

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Inspired by [OpenClaw](https://github.com/openclaw) for computer control concepts
- [OpenAdapt](https://github.com/OpenAdaptAI/OpenAdapt) for recording patterns
- [pynput](https://github.com/moses-palmer/pynput) for input monitoring
