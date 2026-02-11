# Web Interface Guide

Chat with your digital twin through the web interface.

## Starting the Server

```bash
mnemosyne web
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Features

### Chat

Natural language conversation with your digital twin:

> "What did I work on yesterday?"
> "What patterns have you noticed?"
> "Set up my coding environment"

### Dashboard

- Recording status and controls
- Session overview
- Memory statistics

### Configuration

Configure LLM settings directly in the browser:

1. Click **Settings** (gear icon)
2. Select provider (OpenAI, Anthropic, etc.)
3. Enter API key
4. Choose model
5. Click **Save**

### Recording Control

- **Start Recording** - Begin capturing
- **Stop Recording** - End session
- **Status** - View current recording state

### Memory Search

Search your memories from the interface:

1. Type in chat: `@search morning routine`
2. Or use the search bar

## API Documentation

Interactive API docs at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Configuration

```toml
[web]
host = "0.0.0.0"
port = 8000
debug = false
cors_origins = ["*"]
session_timeout = 3600
max_conversations = 100
```

## REST API

### Health Check

```bash
curl http://localhost:8000/health
```

### Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What did I do today?"}'
```

### Memory Search

```bash
curl "http://localhost:8000/api/memories/search?q=morning%20routine"
```

### Recording Control

```bash
# Start
curl -X POST http://localhost:8000/api/recording/start

# Stop
curl -X POST http://localhost:8000/api/recording/stop

# Status
curl http://localhost:8000/api/recording/status
```

## Security

### Local Only

By default, the server binds to `0.0.0.0`. For local-only access:

```toml
[web]
host = "127.0.0.1"
```

### API Keys

Never expose your API keys. The web interface stores them in:
- Browser session (temporary)
- Server config (persistent)

### CORS

Configure allowed origins:

```toml
[web]
cors_origins = ["http://localhost:3000"]
```

## Programmatic Client

See [examples/web_api_client.py](https://github.com/Min-Jihong/mnemosyne/blob/main/examples/web_api_client.py) for a Python client example.
