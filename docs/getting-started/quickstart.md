# Quick Start

Get started with Mnemosyne in 5 minutes.

## Step 1: Setup

Run the interactive setup wizard:

```bash
mnemosyne setup
```

This configures:

- 🔑 LLM provider (OpenAI, Anthropic, Google, Ollama)
- 🤖 Model selection
- 🧠 Curiosity mode

!!! tip "API Keys"
    You'll need an API key from your chosen provider:

    - [OpenAI](https://platform.openai.com/api-keys)
    - [Anthropic](https://console.anthropic.com/)
    - [Google AI](https://makersuite.google.com/app/apikey)
    - Ollama runs locally (no key needed)

## Step 2: Start Web Interface

The easiest way to use Mnemosyne:

```bash
mnemosyne web
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

!!! success "What you can do"
    - 💬 Chat with your digital twin
    - 🔑 Configure LLM settings
    - ⏺️ Control recording
    - 🔍 Search memories

## Step 3: Record Your Activity

### Option A: From Web Interface

Click the **Start Recording** button in the dashboard.

### Option B: From CLI

```bash
mnemosyne record --name "My Work Session"
```

Press `Ctrl+C` to stop recording.

## Step 4: Analyze Your Behavior

After recording a session:

```bash
# List sessions
mnemosyne sessions

# Analyze with AI
mnemosyne analyze <session_id>

# Let AI ask questions
mnemosyne curious <session_id>
```

Example output:

```
🤔 Questions about your session:

1. [HIGH] Why do you always open Slack before checking email?
   Category: workflow | Confidence: 89%

2. [MEDIUM] You typed "git status" 23 times but only committed 3 times. Why?
   Category: habit | Confidence: 72%
```

## Step 5: Search Your Memories

Query your accumulated knowledge:

```bash
mnemosyne memory "how do I usually start my morning"
```

Or use natural language in the web chat:

> "What patterns have you noticed about my coding style?"

## What's Next?

<div class="grid cards" markdown>

-   **Recording Guide**

    Learn about advanced capture options

    [:octicons-arrow-right-24: Recording](../guide/recording.md)

-   **Analysis Guide**

    Deep dive into AI analysis features

    [:octicons-arrow-right-24: Analysis](../guide/analysis.md)

-   **API Reference**

    Build custom integrations

    [:octicons-arrow-right-24: API Docs](../api/index.md)

</div>

## CLI Cheat Sheet

| Command | Description |
|---------|-------------|
| `mnemosyne setup` | Configure settings |
| `mnemosyne web` | Start web interface |
| `mnemosyne record` | Start recording |
| `mnemosyne sessions` | List all sessions |
| `mnemosyne analyze <id>` | AI analysis |
| `mnemosyne curious <id>` | AI questions |
| `mnemosyne memory [query]` | Search memories |
| `mnemosyne status` | Show configuration |
| `mnemosyne version` | Show version |
