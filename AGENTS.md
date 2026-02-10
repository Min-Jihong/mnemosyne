# AGENTS.md - AI Agent Context for Mnemosyne

This document provides context for AI coding assistants (Claude, Copilot, etc.) working on this codebase.

## Project Overview

**Mnemosyne** is a digital twin AI system that learns to think like you by:
1. Recording your computer micro-actions (mouse, keyboard, screen)
2. Inferring intent using LLMs
3. Building semantic memory of your behavior
4. Executing tasks based on learned patterns

## Architecture

```
mnemosyne/
├── capture/      # Input recording (mouse, keyboard, screen, window)
├── store/        # SQLite database and session management
├── reason/       # LLM inference (intent, curious questioning)
├── memory/       # Persistent memory with ChromaDB vectors
├── learn/        # Training pipeline (future ML)
├── execute/      # Computer control agent with safety guards
├── llm/          # Multi-provider abstraction (OpenAI, Anthropic, Google, Ollama)
├── config/       # Pydantic settings
├── cli/          # Typer CLI
└── web/          # FastAPI + embedded chat UI
```

## Key Design Decisions

### 1. Async-First
All I/O operations are async. Use `async/await` patterns:
```python
async def capture_event(self) -> Event:
    ...
```

### 2. Multi-Provider LLM
Never hardcode to a single LLM. Use the factory:
```python
from mnemosyne.llm.factory import LLMFactory
llm = LLMFactory.create(provider="anthropic", model="claude-3-opus")
```

### 3. Type Safety
Use Pydantic models for all data structures:
```python
from pydantic import BaseModel

class Event(BaseModel):
    type: EventType
    timestamp: datetime
    ...
```

### 4. Safety-First Execution
The execute module has multiple safety layers:
- Rate limiting (max actions/minute)
- Blocked apps list
- Blocked hotkeys
- Safe zones (screen regions)
- Emergency stop

## Code Style

- **Python 3.11+** with full type hints
- **Ruff** for linting and formatting
- **MyPy** for type checking
- Line length: 100 characters
- Async functions: use `async def`
- Error handling: use specific exception types

## Testing

- **pytest** with async support
- **70%** coverage threshold
- Test files: `tests/test_*.py`
- Integration tests: `tests/integration/`

Run tests:
```bash
make test        # Basic tests
make test-cov    # With coverage
```

## Common Tasks

### Adding a new LLM provider

1. Create `mnemosyne/llm/providers/newprovider.py`
2. Implement `LLMProvider` base class
3. Register in `mnemosyne/llm/factory.py`
4. Add tests in `tests/test_llm_newprovider.py`

### Adding a new CLI command

1. Add command in `mnemosyne/cli/main.py`
2. Use Typer decorators:
```python
@app.command()
def my_command(arg: str = typer.Argument(...)):
    ...
```

### Adding a new capture type

1. Create handler in `mnemosyne/capture/`
2. Define event type in `mnemosyne/capture/events.py`
3. Register in recorder

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google AI API key |
| `MNEMOSYNE_CONFIG` | Custom config path |
| `MNEMOSYNE_LOG_LEVEL` | Log level (DEBUG, INFO, etc.) |

## Important Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project config, dependencies |
| `mkdocs.yml` | Documentation config |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `Makefile` | Development commands |
| `docker-compose.yml` | Docker setup |

## macOS-Specific

This project has macOS-specific capture code using:
- `pyobjc-framework-Quartz` - Screen capture
- `pyobjc-framework-AppKit` - Window info

These imports are conditional:
```python
try:
    import Quartz
except ImportError:
    Quartz = None
```

## DO NOT

- ❌ Hardcode API keys
- ❌ Use `# type: ignore` without justification
- ❌ Skip async/await for I/O
- ❌ Bypass safety guards in execute module
- ❌ Add dependencies without updating `pyproject.toml`

## DO

- ✅ Use type hints everywhere
- ✅ Write tests for new features
- ✅ Update docs when adding features
- ✅ Use Pydantic for data validation
- ✅ Handle errors gracefully
- ✅ Follow existing code patterns

## Quick Commands

```bash
make install-dev    # Install with dev deps
make test           # Run tests
make lint           # Run linter
make format         # Format code
make typecheck      # Run mypy
make check          # All checks
make web            # Start web server
make docs           # Build docs
```

## Contact

- Issues: GitHub Issues
- Discussions: GitHub Discussions
