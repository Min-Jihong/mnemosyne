# Configuration

Mnemosyne stores configuration in `~/.mnemosyne/config.toml`.

## Configuration File

### Generate Default Config

```bash
mnemosyne setup
```

Or copy the example:

```bash
mkdir -p ~/.mnemosyne
cp examples/config.example.toml ~/.mnemosyne/config.toml
```

### Full Configuration Reference

```toml
# ~/.mnemosyne/config.toml

# =============================================================================
# LLM Provider Configuration
# =============================================================================
[llm]
# Available providers: openai, anthropic, google, ollama
provider = "anthropic"

# Model to use (provider-specific)
# OpenAI: gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo
# Anthropic: claude-3-opus-20240229, claude-3-sonnet-20240229
# Google: gemini-pro, gemini-ultra
# Ollama: llama2, mistral, codellama
model = "claude-3-opus-20240229"

# API key (or use environment variable)
api_key = ""  # Or set ANTHROPIC_API_KEY env var

# Optional: API base URL (for proxies)
# base_url = "https://api.anthropic.com"

# Optional: Request timeout in seconds
# timeout = 30

# =============================================================================
# Curiosity Mode
# =============================================================================
[curiosity]
# How proactive should the AI be?
# - passive: Only answers, doesn't ask questions
# - active: Asks questions after sessions
# - proactive: Constantly curious during recording
mode = "active"

# Minimum importance threshold (0.0 - 1.0)
threshold = 0.7

# Maximum questions per analysis
max_questions = 10

# =============================================================================
# Recording Settings
# =============================================================================
[recording]
# Screenshot settings
screenshot_quality = 80          # JPEG quality (0-100)
screenshot_format = "webp"       # webp, png, jpeg
screenshot_on_click = true
screenshot_on_hotkey = true
screenshot_interval = 0          # Auto-capture (0 = disabled)

# Mouse tracking
mouse_throttle_ms = 50           # Min ms between events
track_mouse_position = true
track_clicks = true
track_scroll = true

# Keyboard tracking
track_keystrokes = true
track_hotkeys = true
track_typing = true              # ⚠️ Careful with sensitive data

# Window tracking
track_window_changes = true
track_window_title = true
track_window_bounds = true

# =============================================================================
# Memory System
# =============================================================================
[memory]
# Vector store settings
embedding_model = "all-MiniLM-L6-v2"
collection_name = "mnemosyne_memories"

# Memory consolidation
auto_consolidate = true
consolidation_interval = 3600    # Seconds

# Retention
max_memories = 100000
importance_decay = 0.1           # Daily decay rate

# =============================================================================
# Execution Agent
# =============================================================================
[execution]
enabled = true
require_confirmation = true

# Rate limiting
max_actions_per_minute = 60
cooldown_between_actions_ms = 100

# Protected apps (never interact)
blocked_apps = [
    "1Password",
    "Keychain Access",
    "System Preferences",
    "Terminal",
]

# Blocked hotkeys
blocked_hotkeys = [
    ["cmd", "q"],
    ["cmd", "shift", "q"],
]

# =============================================================================
# Web Interface
# =============================================================================
[web]
host = "0.0.0.0"
port = 8000
debug = false
cors_origins = ["*"]

# =============================================================================
# Logging
# =============================================================================
[logging]
level = "INFO"                   # DEBUG, INFO, WARNING, ERROR
format = "pretty"                # pretty, json
file = ""                        # Log file path
max_size_mb = 100
backup_count = 5
```

## Environment Variables

You can also use environment variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google AI API key |
| `MNEMOSYNE_CONFIG` | Custom config path |
| `MNEMOSYNE_LOG_LEVEL` | Override log level |

Example:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
mnemosyne web
```

## Provider-Specific Settings

### OpenAI

```toml
[llm]
provider = "openai"
model = "gpt-4-turbo-preview"
api_key = ""  # Or OPENAI_API_KEY env var
```

### Anthropic

```toml
[llm]
provider = "anthropic"
model = "claude-3-opus-20240229"
api_key = ""  # Or ANTHROPIC_API_KEY env var
```

### Google

```toml
[llm]
provider = "google"
model = "gemini-pro"
api_key = ""  # Or GOOGLE_API_KEY env var
```

### Ollama (Local)

```toml
[llm]
provider = "ollama"
model = "llama2"  # or mistral, codellama, mixtral
base_url = "http://localhost:11434"  # Default Ollama URL
```

!!! tip "Running Ollama"
    ```bash
    # Install Ollama
    curl -fsSL https://ollama.com/install.sh | sh

    # Pull a model
    ollama pull llama2

    # Start server (runs automatically)
    ollama serve
    ```
