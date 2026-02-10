"""
Mnemosyne Terminal User Interface (TUI)

A rich, interactive terminal interface built with Textual.

Features:
- Real-time event monitoring
- Session management
- Memory browsing
- Recording controls
- LLM chat interface

Usage:
    mnemosyne tui
"""

from mnemosyne.tui.app import MnemosyneApp

__all__ = ["MnemosyneApp"]
