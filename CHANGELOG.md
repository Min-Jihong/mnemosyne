# Changelog

All notable changes to Mnemosyne will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline with multi-platform testing
- Docker support (Dockerfile and docker-compose.yml)
- Web interface with FastAPI backend and modern chat UI
- LLM API key configuration via web interface
- `mnemosyne web` command to start web server
- CONTRIBUTING.md guide for contributors
- SECURITY.md policy document
- Makefile for common development operations
- install.sh one-liner installation script
- .env.example with all configuration options
- Example configuration file (examples/config.example.toml)
- Issue templates for bug reports and feature requests
- PR template for consistent pull requests

### Changed
- Improved CI with pip caching and concurrency control
- Added Windows support to CI matrix
- README now includes web interface documentation

## [0.1.0] - 2024-02-10

### Added
- Initial release
- **Capture Module**: Mouse, keyboard, screen, and window tracking
  - Mouse: position, clicks, double-clicks, drag, scroll
  - Keyboard: key presses, hotkeys, typing patterns
  - Screen: automatic screenshots on significant actions
  - Window: active app and window title tracking
- **Store Module**: SQLite database with session management
  - Session creation and tracking
  - Event storage with timestamps
  - Screenshot metadata storage
- **Reason Module**: LLM-powered intent inference
  - Intent inference from user actions
  - Curious LLM that asks questions about behavior
  - Pattern detection across sessions
- **Memory Module**: Persistent memory with vector search
  - ChromaDB integration for semantic search
  - Memory consolidation and importance decay
  - Conversation and command memory
- **Learn Module**: Training pipeline for behavior models
  - Dataset creation from recorded sessions
  - Export to JSONL for training
- **Execute Module**: Computer control agent
  - Goal-oriented execution
  - Safety guards (rate limiting, blocked apps)
  - Confirmation mode for careful execution
- **LLM Module**: Multi-provider LLM abstraction
  - OpenAI (GPT-4, GPT-4 Turbo)
  - Anthropic (Claude 3, Claude 3.5)
  - Google (Gemini Pro, Gemini Ultra)
  - Ollama (local models)
- **CLI**: Command-line interface
  - `mnemosyne setup` - Interactive configuration
  - `mnemosyne record` - Start recording
  - `mnemosyne sessions` - List sessions
  - `mnemosyne analyze` - AI intent analysis
  - `mnemosyne curious` - AI curiosity mode
  - `mnemosyne memory` - Search memories
  - `mnemosyne export` - Export for training
  - `mnemosyne execute` - Execute goals
  - `mnemosyne status` - Show configuration

### Security
- Safety guards for execution agent
- Blocked apps list (password managers, system settings)
- Blocked hotkeys (Cmd+Q, etc.)
- Rate limiting for automated actions

[Unreleased]: https://github.com/yourusername/mnemosyne/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/mnemosyne/releases/tag/v0.1.0
