# API Reference

Mnemosyne provides a comprehensive Python API for building custom integrations.

## Quick Start

```python
import asyncio
from mnemosyne import Mnemosyne

async def main():
    # Initialize
    m = Mnemosyne()
    await m.initialize()

    # Record
    session = await m.start_recording("My Session")

    # ... do things ...

    await m.stop_recording()

    # Analyze
    insights = await m.analyze(session.id)

    # Search memories
    memories = await m.search("morning routine")

asyncio.run(main())
```

## Module Overview

| Module | Description |
|--------|-------------|
| [`capture`](capture.md) | Input recording (mouse, keyboard, screen) |
| [`store`](store.md) | Database and session management |
| [`reason`](reason.md) | LLM inference and curiosity |
| [`memory`](memory.md) | Semantic memory system |
| [`execute`](execute.md) | Computer control agent |
| [`llm`](llm.md) | Multi-provider LLM abstraction |

## Core Classes

### Mnemosyne

The main entry point:

```python
from mnemosyne import Mnemosyne

m = Mnemosyne(config_path="~/.mnemosyne/config.toml")
await m.initialize()
```

### RecordingSession

Manages a recording session:

```python
from mnemosyne.capture import RecordingSession

async with RecordingSession("Work") as session:
    await session.wait_until_stopped()
```

### MemoryManager

Access the memory system:

```python
from mnemosyne.memory import MemoryManager

memory = MemoryManager()
await memory.initialize()
results = await memory.search("query")
```

### CuriousLLM

AI analysis engine:

```python
from mnemosyne.reason import CuriousLLM

curious = CuriousLLM(llm_provider)
questions = await curious.observe_and_wonder(events)
```

### ExecutionAgent

Computer control:

```python
from mnemosyne.execute import ExecutionAgent

agent = ExecutionAgent(llm_provider)
await agent.execute("Open Chrome")
```

## Type System

Mnemosyne uses Pydantic for type definitions:

```python
from mnemosyne.capture.events import Event, EventType
from mnemosyne.reason.intent import Intent
from mnemosyne.memory.types import Memory
```

## Async/Await

Mnemosyne is fully async:

```python
import asyncio

async def main():
    # All operations are async
    await mnemosyne.initialize()

asyncio.run(main())
```

## Error Handling

```python
from mnemosyne.exceptions import (
    MnemosyneError,
    ConfigurationError,
    CaptureError,
    LLMError,
)

try:
    await m.initialize()
except ConfigurationError as e:
    print(f"Config issue: {e}")
except LLMError as e:
    print(f"LLM issue: {e}")
```

## Configuration

Access settings programmatically:

```python
from mnemosyne.config import Settings

settings = Settings.load()
print(settings.llm.provider)
print(settings.curiosity.mode)
```
