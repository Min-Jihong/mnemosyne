<div align="center">

# 🧠 Mnemosyne

### *Create Another You*

**Your Digital Clone That Learns How You Think**

[한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh-CN.md) | English

[![CI](https://github.com/Min-Jihong/mnemosyne/actions/workflows/ci.yml/badge.svg)](https://github.com/Min-Jihong/mnemosyne/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/Min-Jihong/mnemosyne?style=social)](https://github.com/Min-Jihong/mnemosyne)
[![GitHub forks](https://img.shields.io/github/forks/Min-Jihong/mnemosyne?style=social)](https://github.com/Min-Jihong/mnemosyne/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/Min-Jihong/mnemosyne?style=social)](https://github.com/Min-Jihong/mnemosyne)
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

<div align="center">

## ⭐ Why Star This Project?

</div>

<table>
<tr>
<td width="50%">

### 🎯 **Not Just Recording — Understanding**
While others capture pixels, Mnemosyne captures **intent**. The AI asks "why?" after every action, building a model of how you think.

### 🔍 **Search Your Past with OCR**
Find that thing you saw last week. OCR indexes every screenshot so you can search by text content.

</td>
<td width="50%">

### 📊 **Know Yourself Better**
AI-generated daily summaries and productivity stats reveal patterns you never noticed about your own behavior.

### ⏪ **Time Travel Your Actions**
Replay any session to see exactly what you did, when, and (thanks to AI) *why*.

</td>
</tr>
</table>

<div align="center">

**The only tool that doesn't just watch you — it *learns to be you*.**

</div>

---

## 🎬 See It In Action

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MNEMOSYNE WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   YOU                          MNEMOSYNE                        OUTPUT      │
│    │                              │                               │         │
│    │  ┌─────────────────┐        │                               │         │
│    ├──│ Click, Type,    │───────►│  📹 CAPTURE                   │         │
│    │  │ Scroll, Switch  │        │  Every micro-action           │         │
│    │  └─────────────────┘        │         │                     │         │
│    │                             │         ▼                     │         │
│    │                             │  🤔 REASON                    │         │
│    │  ┌─────────────────┐        │  "Why did you do that?"       │         │
│    │◄─│ AI asks you     │◄───────│         │                     │         │
│    │  │ curious Qs      │        │         ▼                     │         │
│    │  └─────────────────┘        │  🧠 REMEMBER                  │         │
│    │                             │  Patterns → Memory            │         │
│    │                             │         │                     │         │
│    │                             │         ▼                     │         │
│    │                             │  ┌─────────────────────────┐  │         │
│    │                             │  │ 📊 Daily Summary        │──┼────►    │
│    │                             │  │ 🔍 OCR Search           │  │         │
│    │                             │  │ ⏪ Action Replay        │  │         │
│    │                             │  │ 🤖 Execute Goals        │  │         │
│    │                             │  └─────────────────────────┘  │         │
│    │                                                             │         │
└────┴─────────────────────────────────────────────────────────────┴─────────┘

$ mnemosyne summary today
┌──────────────────────────────────────────────────────────────────┐
│  📊 YOUR DAY AT A GLANCE                        Feb 11, 2026     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ⏱️  Active Time: 6h 42m                                         │
│  🖱️  Clicks: 2,847  |  ⌨️  Keystrokes: 18,392                    │
│  🔄  App Switches: 234  |  📸 Screenshots: 89                    │
│                                                                  │
│  🏆 TOP APPS                    🧠 AI INSIGHTS                   │
│  ├─ VS Code      3h 12m        "You context-switch less on      │
│  ├─ Chrome       1h 45m         Tuesdays. Consider blocking      │
│  ├─ Slack          38m          Slack until noon?"               │
│  └─ Terminal       27m                                           │
│                                                                  │
│  💡 "You typed 'git status' 47 times but only committed 5x.     │
│      That's a 9:1 check-to-commit ratio. Anxiety or process?"   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
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

## 🏆 How We Compare

| Feature | Mnemosyne | Screenpipe | OpenAdapt | Rewind |
|---------|:---------:|:----------:|:---------:|:------:|
| **Micro-action capture** | ✅ | ❌ | ✅ | ❌ |
| **Intent inference (Why?)** | ✅ | ❌ | ❌ | ❌ |
| **Curious AI questioning** | ✅ | ❌ | ❌ | ❌ |
| **OCR text search** | ✅ | ✅ | ❌ | ✅ |
| **AI daily summaries** | ✅ | ❌ | ❌ | ❌ |
| **Action replay** | ✅ | ❌ | ✅ | ❌ |
| **Semantic memory** | ✅ | ❌ | ❌ | ❌ |
| **Goal execution** | ✅ | ❌ | ✅ | ❌ |
| **Multi-LLM support** | ✅ | ❌ | ✅ | ❌ |
| **Local-first / Privacy** | ✅ | ✅ | ✅ | ❌ |
| **Privacy scrubbing (PII)** | ✅ | ❌ | ✅ | ❌ |
| **Visual grounding (Set-of-Mark)** | ✅ | ❌ | ✅ | ❌ |
| **Event aggregation** | ✅ | ❌ | ✅ | ❌ |
| **Open source** | ✅ | ✅ | ✅ | ❌ |

**Screenpipe** = Audio/video focus | **OpenAdapt** = Visual grounding RPA | **Rewind** = OCR search (closed source)

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

### 📊 Analytics & Insights
**NEW!** Understand your work patterns like never before:

```bash
# Get an AI-generated summary of your day
$ mnemosyne summary today

📊 Daily Summary - February 11, 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Main Focus: Backend API development
   You spent 68% of active time in VS Code working on auth module.

💡 Key Insight: Your most productive hours were 9-11am.
   Consider scheduling deep work during this window.

⚠️  Pattern Alert: 12 context switches in 30 minutes after lunch.
   This correlates with lower code output.

# Get detailed productivity statistics
$ mnemosyne stats week

📈 Weekly Statistics
├─ Total Active Time: 34h 12m
├─ Most Used App: VS Code (18h 45m)
├─ Peak Productivity: Tuesday 9:00-11:30am
├─ Avg Session Length: 47 minutes
└─ Focus Score: 7.2/10 (↑ 0.8 from last week)
```

### 🔍 OCR Search
**NEW!** Find anything you've ever seen on screen:

```bash
# Search for text across all your screenshots
$ mnemosyne search "API_KEY"

🔍 Found 3 matches:

1. [Feb 10, 14:32] VS Code - .env file
   "OPENAI_API_KEY=sk-..."
   
2. [Feb 9, 11:15] Chrome - OpenAI Dashboard
   "Your API_KEY has been rotated"
   
3. [Feb 8, 16:45] Slack - #dev channel
   "Can someone share the API_KEY for staging?"
```

### ⏪ Action Replay
**NEW!** Time-travel through your sessions:

```bash
# Replay a recorded session
$ mnemosyne replay ses_abc123

⏪ Replaying session: "Morning Coding" (Feb 10, 2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[09:00:15] 🖱️  Click: VS Code icon in dock
[09:00:16] ⌨️  Hotkey: Cmd+Shift+P (Command Palette)
[09:00:18] ⌨️  Type: "git pull"
[09:00:19] 🖱️  Click: Terminal panel
           💭 Intent: "Syncing latest changes before starting work"
[09:00:25] ⌨️  Hotkey: Cmd+P (Quick Open)
[09:00:27] ⌨️  Type: "auth.py"
           💭 Intent: "Continuing work on authentication module"

Controls: [Space] Pause | [←/→] Step | [Q] Quit | [S] Speed
```

### 🔒 Privacy Scrubbing
**NEW!** Automatic PII detection and masking:

```bash
# Check privacy settings
$ mnemosyne privacy status

🔒 Privacy Scrubbing: ENABLED
   Level: standard
   PII Types: email, phone, ssn, credit_card, api_key, password

# Test PII detection
$ mnemosyne privacy test "Contact john@email.com or call 555-123-4567"

🔍 PII Detected:
   [EMAIL] john@email.com → [EMAIL_REDACTED]
   [PHONE] 555-123-4567 → [PHONE_REDACTED]

# Scrub a file
$ mnemosyne privacy scrub-file ./notes.txt
✅ Scrubbed 3 PII instances → ./notes.scrubbed.txt
```

**Supported PII Types:**
- 📧 Email addresses
- 📞 Phone numbers
- 🆔 SSN / National IDs
- 💳 Credit card numbers
- 🔑 API keys & secrets
- 🔐 Passwords (in URLs, configs)
- 🌐 IP & MAC addresses

### 🎯 Visual Grounding (Set-of-Mark)
**NEW!** AI-powered UI element detection for computer control:

```bash
# Detect UI elements in a screenshot
$ mnemosyne ground screenshot.png --prompt

🎯 UI Elements Detected: 12

[1] BUTTON @ (145, 230) - "Submit"
[2] INPUT @ (120, 180) - text field
[3] LINK @ (50, 320) - "Learn more"
[4] BUTTON @ (290, 230) - "Cancel"
...

📝 Set-of-Mark Prompt Generated:
"The screenshot shows a form with the following interactive elements:
 [1] Submit button at top-right
 [2] Text input field for email
 [3] 'Learn more' link at bottom
 [4] Cancel button next to Submit
 
 To submit the form, click element [1]."
```

### 📦 Event Aggregation
**NEW!** Reduce noise by merging repetitive events:

```bash
# Aggregate events in a session
$ mnemosyne aggregate ses_abc123

📦 Aggregation Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Original events: 15,847
   Aggregated:      1,234
   Compression:     92.2%

   🖱️  Mouse movements: 12,456 → 89 trajectories
   📜 Scroll events:   1,203 → 45 scroll actions
   ⌨️  Keystrokes:      2,188 → 156 typing segments
   
   💾 Storage saved: 14.2 MB → 1.1 MB
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
git clone https://github.com/Min-Jihong/mnemosyne.git
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
| | |
| **📊 Analytics** | |
| `mnemosyne summary [today\|yesterday\|week]` | AI-generated daily/weekly summaries |
| `mnemosyne stats [today\|yesterday\|week]` | Work statistics and productivity metrics |
| | |
| **🔍 Search & Replay** | |
| `mnemosyne search <query>` | OCR text search across screenshots |
| `mnemosyne replay <session_id>` | Replay recorded actions with intent |
| | |
| **🔒 Privacy & Processing** | |
| `mnemosyne privacy status` | Show privacy scrubbing settings |
| `mnemosyne privacy enable/disable` | Toggle PII scrubbing |
| `mnemosyne privacy level [aggressive\|standard\|minimal]` | Set scrubbing level |
| `mnemosyne privacy test <text>` | Test PII detection |
| `mnemosyne ground <image>` | Detect UI elements (Set-of-Mark) |
| `mnemosyne aggregate <session_id>` | Compress repetitive events |

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
├── analytics/    # Summary generation and statistics
├── ocr/          # Screenshot text extraction and search
├── replay/       # Session playback engine
├── privacy/      # PII detection and scrubbing
├── grounding/    # Visual UI element detection (Set-of-Mark)
├── aggregation/  # Event compression and path simplification
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

---

<div align="center">

**If Mnemosyne helps you understand yourself better, consider giving it a ⭐**

*Built with curiosity by humans who wanted to know themselves better.*

</div>