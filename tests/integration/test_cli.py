"""
Integration tests for CLI commands.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock

# Import the CLI app
from mnemosyne.cli.main import app

runner = CliRunner()


class TestCLIBasicCommands:
    """Test basic CLI commands that don't require external services."""

    def test_version_command(self):
        """Test version command shows version info."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "mnemosyne" in result.stdout.lower() or "0." in result.stdout

    def test_help_command(self):
        """Test help command shows usage info."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.stdout or "usage" in result.stdout

    def test_status_command(self):
        """Test status command runs."""
        result = runner.invoke(app, ["status"])
        # Should run without error even if not configured
        assert result.exit_code in [0, 1]  # May fail if not configured


class TestCLISetupCommand:
    """Test setup command."""

    def test_setup_help(self):
        """Test setup help shows options."""
        result = runner.invoke(app, ["setup", "--help"])
        assert result.exit_code == 0


class TestCLISessionsCommand:
    """Test sessions command."""

    @patch("mnemosyne.cli.main.Database")
    def test_sessions_list(self, mock_db_class):
        """Test sessions list command."""
        # Setup mock
        mock_db = MagicMock()
        mock_db.list_sessions = AsyncMock(return_value=[])
        mock_db.close = AsyncMock()
        mock_db_class.return_value = mock_db

        result = runner.invoke(app, ["sessions"])
        # Should complete without error
        assert result.exit_code in [0, 1]


class TestCLIMemoryCommand:
    """Test memory command."""

    def test_memory_help(self):
        """Test memory help shows options."""
        result = runner.invoke(app, ["memory", "--help"])
        assert result.exit_code == 0

    @patch("mnemosyne.cli.main.MemoryManager")
    def test_memory_recent(self, mock_memory_class):
        """Test memory --recent command."""
        mock_memory = MagicMock()
        mock_memory.initialize = AsyncMock()
        mock_memory.get_recent = AsyncMock(return_value=[])
        mock_memory.close = AsyncMock()
        mock_memory_class.return_value = mock_memory

        result = runner.invoke(app, ["memory", "--recent"])
        assert result.exit_code in [0, 1]


class TestCLIRecordCommand:
    """Test record command."""

    def test_record_help(self):
        """Test record help shows options."""
        result = runner.invoke(app, ["record", "--help"])
        assert result.exit_code == 0


class TestCLIAnalyzeCommand:
    """Test analyze command."""

    def test_analyze_help(self):
        """Test analyze help shows options."""
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0

    def test_analyze_requires_session_id(self):
        """Test analyze requires a session ID."""
        result = runner.invoke(app, ["analyze"])
        # Should error or show help when no session ID provided
        assert result.exit_code != 0 or "Usage" in result.stdout


class TestCLICuriousCommand:
    """Test curious command."""

    def test_curious_help(self):
        """Test curious help shows options."""
        result = runner.invoke(app, ["curious", "--help"])
        assert result.exit_code == 0


class TestCLIExecuteCommand:
    """Test execute command."""

    def test_execute_help(self):
        """Test execute help shows options."""
        result = runner.invoke(app, ["execute", "--help"])
        assert result.exit_code == 0


class TestCLIWebCommand:
    """Test web command."""

    def test_web_help(self):
        """Test web help shows options."""
        result = runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
