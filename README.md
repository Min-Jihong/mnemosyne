# Mnemosyne

[한국어](README.ko.md) | English

> **Learn to Think Like You** - A digital twin that learns your computer behavior and thought patterns

Mnemosyne is an AI-powered system that records your computer interactions, analyzes WHY you perform each action, and eventually learns to think and act like you.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MNEMOSYNE ARCHITECTURE                          │
│                    "Learn to Think Like You"                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   CAPTURE    │───▶│   REASON     │───▶│   LEARN      │              │
│  │   Layer      │    │   Layer      │    │   Layer      │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ Mouse/Key/   │    │ LLM Intent   │    │ Behavior     │              │
│  │ Screen/Audio │    │ Inference    │    │ Transformer  │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                 │                       │
│                                                 ▼                       │
│                                          ┌──────────────┐              │
│                                          │   EXECUTE    │              │
│                                          │   Layer      │              │
│                                          └──────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

### 🎯 Micro-Action Recording
- **Mouse tracking**: Movements, clicks, double-clicks, drag, scroll
- **Keyboard capture**: Key presses, hotkeys, typing patterns
- **Screen capture**: Automatic screenshots on actions
- **Window context**: Active app and window title tracking

### 🧠 Curious LLM
Unlike passive analysis, Mnemosyne's LLM actively:
- **Asks questions** about your behavior patterns
- **Finds patterns** in how you work
- **Generates insights** about your habits and preferences

### 💾 Persistent Memory (OpenClaw-style)
- Remembers all commands and conversations
- Semantic search across memories
- Memory consolidation for higher-level insights
- ChromaDB vector store for fast retrieval

### 🤖 Execution Agent
- Goal-oriented computer control
- Safety guards with rate limiting
- Protected apps and hotkeys
- Confirmation mode for careful execution

### 🔌 Multi-Provider LLM Support
- OpenAI (GPT-4, GPT-4V)
- Anthropic (Claude 3)
- Google (Gemini)
- Ollama (Local models)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mnemosyne.git
cd mnemosyne

# Install with pip
pip install -e .

# For macOS native capture (recommended)
pip install -e ".[macos]"

# For ML training capabilities
pip install -e ".[ml]"
```

### macOS Permissions

Mnemosyne requires the following permissions:
- **Accessibility**: System Preferences → Security & Privacy → Privacy → Accessibility
- **Input Monitoring**: System Preferences → Security & Privacy → Privacy → Input Monitoring
- **Screen Recording**: System Preferences → Security & Privacy → Privacy → Screen Recording

## Quick Start

### 1. Setup

```bash
mnemosyne setup
```

This interactive wizard will configure:
- LLM provider and API key
- Model selection
- Curiosity mode settings

### 2. Record Your Activity

```bash
# Start recording
mnemosyne record --name "My Work Session"

# Press Ctrl+C to stop
```

### 3. Analyze with LLM

```bash
# Infer intent for recorded actions
mnemosyne analyze <session-id>

# Let the curious LLM ask questions
mnemosyne curious <session-id>
```

### 4. Browse Memory

```bash
# Search memories
mnemosyne memory "how I usually start my day"

# Show recent memories
mnemosyne memory --recent
```

### 5. Execute Goals

```bash
# Let Mnemosyne act based on learned behavior
mnemosyne execute "Open my usual morning apps"
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `mnemosyne setup` | Interactive configuration wizard |
| `mnemosyne record` | Start recording computer activity |
| `mnemosyne sessions` | List recorded sessions |
| `mnemosyne analyze <id>` | Analyze session with LLM |
| `mnemosyne curious <id>` | Let LLM explore and ask questions |
| `mnemosyne memory [query]` | Search or browse memories |
| `mnemosyne export <id>` | Export session for training |
| `mnemosyne execute <goal>` | Execute a goal |
| `mnemosyne status` | Show configuration |
| `mnemosyne version` | Show version |

## Configuration

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

## Project Structure

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
└── cli/          # Command-line interface
```

## How It Works

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

## Safety Features

Mnemosyne includes multiple safety mechanisms:

- **Rate limiting**: Max 60 actions/minute by default
- **Blocked apps**: Terminal, Password managers, System Preferences
- **Blocked hotkeys**: Cmd+Q, Cmd+Shift+Q, etc.
- **Safe zones**: Restrict actions to specific screen areas
- **Emergency stop**: Immediate halt of all actions

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [OpenClaw](https://github.com/openclaw) for computer control concepts
- [OpenAdapt](https://github.com/OpenAdaptAI/OpenAdapt) for recording patterns
- [pynput](https://github.com/moses-palmer/pynput) for input monitoring
