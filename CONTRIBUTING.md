# Contributing to Mnemosyne

Thank you for your interest in contributing to Mnemosyne! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- macOS (for full capture functionality) or Linux/Windows (limited functionality)

### Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/mnemosyne.git
   cd mnemosyne
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode**

   ```bash
   pip install -e ".[dev,web]"
   ```

4. **Run the tests**

   ```bash
   pytest tests/ -v
   ```

5. **Start the development server**

   ```bash
   mnemosyne web --reload
   ```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-new-llm-provider`
- `fix/memory-leak-in-recorder`
- `docs/update-installation-guide`
- `refactor/simplify-event-handling`

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(llm): add support for Mistral AI provider
fix(capture): resolve memory leak in mouse tracker
docs(readme): add Docker installation instructions
```

## Pull Request Process

1. **Create a feature branch** from `main`

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit them

3. **Ensure all tests pass**

   ```bash
   pytest tests/ -v
   ```

4. **Run linting**

   ```bash
   ruff check mnemosyne/
   ruff format mnemosyne/
   ```

5. **Push your branch**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** on GitHub

7. **Address review feedback** if any

### PR Requirements

- [ ] All tests pass
- [ ] Code follows project style guidelines
- [ ] Documentation is updated (if needed)
- [ ] Commit messages follow conventions
- [ ] No merge conflicts with `main`

## Coding Standards

### Python Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
ruff check mnemosyne/

# Auto-fix issues
ruff check --fix mnemosyne/

# Format code
ruff format mnemosyne/
```

### Type Hints

All functions should have type hints:

```python
def process_event(event: MouseClickEvent, context: dict[str, Any]) -> ProcessedEvent:
    """Process a mouse click event with context."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def remember(
    self,
    content: str,
    memory_type: MemoryType = MemoryType.OBSERVATION,
    importance: float = 0.5,
) -> Memory:
    """Store a new memory.

    Args:
        content: The content to remember.
        memory_type: Type of memory (default: OBSERVATION).
        importance: Importance score from 0.0 to 1.0.

    Returns:
        The created Memory object.

    Raises:
        ValueError: If importance is not between 0.0 and 1.0.
    """
    ...
```

### Imports

Order imports as follows:

1. Standard library
2. Third-party packages
3. Local imports

```python
import json
from pathlib import Path
from typing import Any

import anthropic
from pydantic import BaseModel

from mnemosyne.llm.base import LLMProvider
from mnemosyne.memory.types import Memory
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=mnemosyne --cov-report=html

# Run specific test file
pytest tests/test_memory.py -v

# Run specific test
pytest tests/test_memory.py::TestPersistentMemory::test_remember -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use fixtures from `conftest.py`

```python
import pytest
from mnemosyne.memory.persistent import PersistentMemory

class TestPersistentMemory:

    def test_remember(self, temp_dir):
        """Test that memories can be stored and retrieved."""
        mem = PersistentMemory(data_dir=temp_dir)
        
        memory = mem.remember(content="Test content")
        
        assert memory.id is not None
        assert mem.count() == 1
```

## Documentation

### Updating Documentation

- **README.md**: For user-facing changes
- **ARCHITECTURE.md**: For architectural changes
- **Docstrings**: For API documentation

### Building Docs

```bash
# If using mkdocs (future)
mkdocs serve
```

## Questions?

If you have questions:

1. Check existing issues and discussions
2. Open a new issue with the `question` label
3. Join our community (Discord/Slack - TBD)

Thank you for contributing to Mnemosyne! 🧠
