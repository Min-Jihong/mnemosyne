# Mnemosyne Examples

This directory contains example scripts demonstrating how to use Mnemosyne
programmatically.

## Prerequisites

Install Mnemosyne with all features:

```bash
pip install -e ".[all]"
```

On macOS, grant necessary permissions:
- System Settings → Privacy & Security → Accessibility
- System Settings → Privacy & Security → Input Monitoring
- System Settings → Privacy & Security → Screen Recording

## Examples

### 1. Basic Recording (`basic_recording.py`)

Demonstrates how to start a recording session and capture computer activity.

```bash
python examples/basic_recording.py
```

This will:
- Start capturing mouse, keyboard, and window events
- Take screenshots on significant actions
- Save all events to the database
- Print a summary when stopped (Ctrl+C)

### 2. Session Analysis (`analyze_session.py`)

Analyze recorded sessions using AI to understand behavior patterns.

```bash
# List available sessions
python examples/analyze_session.py --list

# Analyze a specific session
python examples/analyze_session.py <session_id>
```

Features:
- Intent inference for each action
- Curious AI questioning
- Behavior pattern detection
- Session summary generation

### 3. Memory Search (`memory_search.py`)

Search through your accumulated memories and insights.

```bash
# Semantic search
python examples/memory_search.py "morning routine"
python examples/memory_search.py "git workflow"

# Show recent memories
python examples/memory_search.py --recent

# Show important memories
python examples/memory_search.py --important

# Show statistics
python examples/memory_search.py --stats
```

### 4. Web API Client (`web_api_client.py`)

Interact with Mnemosyne's REST API programmatically.

```bash
# First, start the web server
mnemosyne web

# Then run the client
python examples/web_api_client.py
```

This demonstrates:
- Health checks
- LLM configuration
- Chat with digital twin
- Memory search via API
- Recording control

### 5. Configuration (`config.example.toml`)

Example configuration file with all available options.

```bash
# Copy to your config directory
cp examples/config.example.toml ~/.mnemosyne/config.toml

# Edit as needed
vim ~/.mnemosyne/config.toml
```

## Quick Start Guide

1. **Setup** - Configure your LLM provider:
   ```bash
   mnemosyne setup
   ```

2. **Record** - Start capturing your activity:
   ```bash
   python examples/basic_recording.py
   # Or use CLI: mnemosyne record
   ```

3. **Analyze** - Understand your behavior:
   ```bash
   python examples/analyze_session.py <session_id>
   ```

4. **Search** - Query your memories:
   ```bash
   python examples/memory_search.py "how do I usually..."
   ```

5. **Chat** - Talk to your digital twin:
   ```bash
   mnemosyne web
   # Open http://localhost:8000
   ```

## API Reference

For full API documentation, start the web server and visit:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Troubleshooting

### Permission Denied (macOS)

Grant accessibility permissions:
1. Open System Settings
2. Go to Privacy & Security
3. Enable access for Terminal/your IDE

### LLM Not Configured

Run the setup wizard:
```bash
mnemosyne setup
```

Or configure directly in `~/.mnemosyne/config.toml`

### No Memories Found

1. Record some sessions first
2. Analyze them to generate memories
3. Memories accumulate over time

## More Information

- [Main Documentation](../README.md)
- [Architecture Guide](../ARCHITECTURE.md)
- [Contributing Guide](../CONTRIBUTING.md)
