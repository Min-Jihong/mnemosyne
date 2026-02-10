# Testing Guide

Guidelines for testing Mnemosyne.

## Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=mnemosyne --cov-report=html

# Specific test file
pytest tests/test_database.py

# Verbose output
pytest tests/ -v
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_database.py     # Database tests
├── test_events.py       # Event handling tests
├── test_memory.py       # Memory system tests
├── test_safety.py       # Safety guard tests
└── integration/         # Integration tests
```

## Writing Tests

### Unit Tests

```python
import pytest
from mnemosyne.capture.events import Event, EventType

def test_event_creation():
    event = Event(
        type=EventType.MOUSE_CLICK,
        timestamp=datetime.now(),
        x=100,
        y=200,
    )
    assert event.type == EventType.MOUSE_CLICK
    assert event.x == 100
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_database_session():
    db = Database()
    session_id = await db.create_session("test")
    assert session_id is not None
    await db.close()
```

### Fixtures

```python
# conftest.py
import pytest

@pytest.fixture
async def database():
    db = Database(":memory:")
    await db.initialize()
    yield db
    await db.close()

# Usage
async def test_with_db(database):
    session = await database.create_session("test")
```

## Coverage Requirements

- Minimum: 50% (CI enforced)
- Target: 80%

Check coverage:

```bash
pytest tests/ --cov=mnemosyne --cov-report=term-missing
```

## Mocking

### LLM Provider

```python
from unittest.mock import AsyncMock

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate.return_value = "Test response"
    return llm
```

### External APIs

```python
import responses

@responses.activate
def test_api_call():
    responses.add(
        responses.GET,
        "https://api.example.com",
        json={"result": "ok"},
    )
    # Test code here
```
