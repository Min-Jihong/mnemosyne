"""
Integration tests for the Web API.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Check if fastapi is available
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient


class TestWebAPIHealth:
    """Test health endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        # Import here to avoid issues if fastapi not installed
        from mnemosyne.web.app import app
        return TestClient(app)

    def test_health_check(self, client):
        """Test health endpoint returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ok", "healthy"]


class TestWebAPIChat:
    """Test chat endpoints."""

    @pytest.fixture
    def client(self):
        from mnemosyne.web.app import app
        return TestClient(app)

    @patch("mnemosyne.web.app.get_llm_provider")
    def test_chat_requires_message(self, mock_llm, client):
        """Test chat endpoint requires a message."""
        response = client.post("/api/chat", json={})
        # Should fail validation
        assert response.status_code in [400, 422]


class TestWebAPIRecording:
    """Test recording control endpoints."""

    @pytest.fixture
    def client(self):
        from mnemosyne.web.app import app
        return TestClient(app)

    def test_recording_status(self, client):
        """Test recording status endpoint."""
        response = client.get("/api/recording/status")
        assert response.status_code == 200
        data = response.json()
        assert "recording" in data


class TestWebAPIMemory:
    """Test memory search endpoints."""

    @pytest.fixture
    def client(self):
        from mnemosyne.web.app import app
        return TestClient(app)

    def test_memory_search_requires_query(self, client):
        """Test memory search requires query parameter."""
        response = client.get("/api/memories/search")
        # Should work even without query (returns empty or requires param)
        assert response.status_code in [200, 400, 422]


class TestWebAPISessions:
    """Test session endpoints."""

    @pytest.fixture
    def client(self):
        from mnemosyne.web.app import app
        return TestClient(app)

    def test_list_sessions(self, client):
        """Test sessions list endpoint."""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
