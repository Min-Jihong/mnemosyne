# Memory Guide

Mnemosyne's semantic memory system stores and retrieves your behavioral patterns.

## Overview

Unlike traditional databases, Mnemosyne uses **semantic search**—finding memories by meaning, not keywords.

## Searching Memories

### CLI

```bash
# Semantic search
mnemosyne memory "how do I usually start my morning"

# Recent memories
mnemosyne memory --recent

# Important memories
mnemosyne memory --important
```

### Web Interface

Use the chat to ask questions:

> "What patterns have you noticed about my work habits?"

## Memory Types

| Type | Description |
|------|-------------|
| `action` | Individual captured actions |
| `intent` | Inferred purposes |
| `pattern` | Detected behavioral patterns |
| `insight` | AI-generated observations |
| `answer` | Your explanations |

## How Memory Works

### 1. Capture

Events are recorded during sessions.

### 2. Analysis

AI processes events to extract meaning.

### 3. Embedding

Memories are converted to vectors for semantic search.

### 4. Consolidation

Related memories are combined into insights.

### 5. Retrieval

Semantic search finds relevant memories.

## Memory Consolidation

Mnemosyne automatically consolidates memories:

```toml
[memory]
auto_consolidate = true
consolidation_interval = 3600  # Every hour
```

Consolidation:
- Groups related memories
- Generates higher-level insights
- Prunes redundant information

## Importance Decay

Memories lose importance over time:

```toml
[memory]
importance_decay = 0.1  # 10% daily decay
```

This ensures recent memories are prioritized.

## Programmatic Access

```python
from mnemosyne.memory import MemoryManager

memory = MemoryManager()
await memory.initialize()

# Semantic search
results = await memory.search("morning routine", limit=10)

# Recent memories
recent = await memory.get_recent(days=7)

# Important memories
important = await memory.get_important(threshold=0.8)

# Statistics
stats = await memory.get_stats()
```

## Storage Backend

Mnemosyne uses ChromaDB for vector storage:

```toml
[memory]
embedding_model = "all-MiniLM-L6-v2"
collection_name = "mnemosyne_memories"
max_memories = 100000
```

## Data Location

Memories are stored in:

```
~/.mnemosyne/
├── data/
│   ├── mnemosyne.db      # SQLite database
│   └── chroma/           # Vector store
```

## Backup & Export

```bash
# Export all memories
mnemosyne export-memories --format json > memories.json

# Backup database
cp -r ~/.mnemosyne/data ./backup/
```
