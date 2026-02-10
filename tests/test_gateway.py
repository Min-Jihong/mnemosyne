"""Tests for the WebSocket Gateway."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from mnemosyne.web.gateway import (
    Gateway,
    GatewayClient,
    GatewayEvent,
    GatewayEventType,
    ConnectionState,
)


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.sent_messages: list[str] = []

    async def send_text(self, message: str) -> None:
        self.sent_messages.append(message)


class TestGateway:
    """Tests for the Gateway class."""

    @pytest.fixture
    def gateway(self) -> Gateway:
        """Create a fresh gateway."""
        return Gateway(heartbeat_interval=1.0, heartbeat_timeout=3.0)

    @pytest.fixture
    def mock_websocket(self) -> MockWebSocket:
        """Create a mock WebSocket."""
        return MockWebSocket()

    @pytest.mark.asyncio
    async def test_connect_client(
        self, gateway: Gateway, mock_websocket: MockWebSocket
    ) -> None:
        """Test connecting a new client."""
        client = await gateway.connect(mock_websocket, client_id="test-client")

        assert client.client_id == "test-client"
        assert client.state == ConnectionState.CONNECTING
        assert gateway.client_count == 1
        assert len(mock_websocket.sent_messages) == 1  # HELLO event

    @pytest.mark.asyncio
    async def test_disconnect_client(
        self, gateway: Gateway, mock_websocket: MockWebSocket
    ) -> None:
        """Test disconnecting a client."""
        await gateway.connect(mock_websocket, client_id="test-client")
        await gateway.disconnect("test-client", reason="test")

        assert gateway.client_count == 0

    @pytest.mark.asyncio
    async def test_handle_heartbeat(
        self, gateway: Gateway, mock_websocket: MockWebSocket
    ) -> None:
        """Test heartbeat handling."""
        client = await gateway.connect(mock_websocket)

        original_heartbeat = client.last_heartbeat

        # Wait a tiny bit so times are different
        await asyncio.sleep(0.01)

        response = await gateway.handle_message(
            client.client_id,
            {"type": "heartbeat", "payload": {}},
        )

        assert response is not None
        assert response.type == GatewayEventType.HEARTBEAT_ACK
        assert client.last_heartbeat > original_heartbeat

    @pytest.mark.asyncio
    async def test_handle_identify(
        self, gateway: Gateway, mock_websocket: MockWebSocket
    ) -> None:
        """Test client identification."""
        client = await gateway.connect(mock_websocket)

        response = await gateway.handle_message(
            client.client_id,
            {
                "type": "identify",
                "payload": {
                    "user_id": "user-123",
                    "device_type": "desktop",
                },
            },
        )

        assert response is not None
        assert response.type == GatewayEventType.READY
        assert client.user_id == "user-123"
        assert client.device_type == "desktop"
        assert client.state == ConnectionState.READY

    @pytest.mark.asyncio
    async def test_send_to_client(
        self, gateway: Gateway, mock_websocket: MockWebSocket
    ) -> None:
        """Test sending event to a specific client."""
        client = await gateway.connect(mock_websocket)

        # Identify to set state to READY
        await gateway.handle_message(
            client.client_id,
            {"type": "identify", "payload": {"user_id": "user-123"}},
        )

        # Clear previous messages
        mock_websocket.sent_messages.clear()

        result = await gateway.send(
            client.client_id,
            GatewayEventType.SYSTEM,
            {"message": "test"},
        )

        assert result is True
        assert len(mock_websocket.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_broadcast(self, gateway: Gateway) -> None:
        """Test broadcasting to multiple clients."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        ws3 = MockWebSocket()

        client1 = await gateway.connect(ws1, client_id="client-1")
        client2 = await gateway.connect(ws2, client_id="client-2")
        client3 = await gateway.connect(ws3, client_id="client-3")

        # Identify all clients
        for client_id in ["client-1", "client-2", "client-3"]:
            await gateway.handle_message(
                client_id,
                {"type": "identify", "payload": {"user_id": f"user-{client_id}"}},
            )

        # Clear previous messages
        ws1.sent_messages.clear()
        ws2.sent_messages.clear()
        ws3.sent_messages.clear()

        count = await gateway.broadcast(
            GatewayEventType.SYSTEM,
            {"message": "broadcast test"},
        )

        assert count == 3
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1
        assert len(ws3.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_broadcast_with_exclude(self, gateway: Gateway) -> None:
        """Test broadcasting with exclusions."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await gateway.connect(ws1, client_id="client-1")
        await gateway.connect(ws2, client_id="client-2")

        # Identify clients
        for client_id in ["client-1", "client-2"]:
            await gateway.handle_message(
                client_id,
                {"type": "identify", "payload": {"user_id": f"user-{client_id}"}},
            )

        ws1.sent_messages.clear()
        ws2.sent_messages.clear()

        count = await gateway.broadcast(
            GatewayEventType.SYSTEM,
            {"message": "test"},
            exclude=["client-1"],
        )

        assert count == 1
        assert len(ws1.sent_messages) == 0
        assert len(ws2.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_sequence_numbers(self, gateway: Gateway) -> None:
        """Test that sequence numbers increment."""
        ws = MockWebSocket()
        client = await gateway.connect(ws)

        await gateway.handle_message(
            client.client_id,
            {"type": "identify", "payload": {"user_id": "user-1"}},
        )

        ws.sent_messages.clear()

        # Send multiple events
        await gateway.send(client.client_id, GatewayEventType.SYSTEM, {"n": 1})
        await gateway.send(client.client_id, GatewayEventType.SYSTEM, {"n": 2})
        await gateway.send(client.client_id, GatewayEventType.SYSTEM, {"n": 3})

        # Parse and check sequence numbers
        import json
        events = [json.loads(m) for m in ws.sent_messages]

        assert events[0]["seq"] < events[1]["seq"]
        assert events[1]["seq"] < events[2]["seq"]

    @pytest.mark.asyncio
    async def test_event_history(self, gateway: Gateway) -> None:
        """Test event history for gap recovery."""
        ws = MockWebSocket()
        client = await gateway.connect(ws)

        await gateway.handle_message(
            client.client_id,
            {"type": "identify", "payload": {"user_id": "user-1"}},
        )

        # Broadcast some events
        await gateway.broadcast(GatewayEventType.SYSTEM, {"n": 1})
        await gateway.broadcast(GatewayEventType.SYSTEM, {"n": 2})
        await gateway.broadcast(GatewayEventType.SYSTEM, {"n": 3})

        # Get events since sequence 1
        events = await gateway.get_events_since(1)
        # Should have at least the last 2 system events (seq > 1)
        assert len(events) >= 2

    @pytest.mark.asyncio
    async def test_error_on_invalid_json(
        self, gateway: Gateway, mock_websocket: MockWebSocket
    ) -> None:
        """Test error response for invalid JSON."""
        client = await gateway.connect(mock_websocket)

        response = await gateway.handle_message(
            client.client_id,
            "not valid json",
        )

        assert response is not None
        assert response.type == GatewayEventType.ERROR
        assert response.payload["code"] == 4001

    @pytest.mark.asyncio
    async def test_on_event_decorator(
        self, gateway: Gateway, mock_websocket: MockWebSocket
    ) -> None:
        """Test event handler decorator."""
        handler_called = False

        @gateway.on_event(GatewayEventType.CHAT_MESSAGE)
        async def handle_chat(client, event):
            nonlocal handler_called
            handler_called = True
            return GatewayEvent(
                type=GatewayEventType.CHAT_MESSAGE,
                payload={"echo": event.payload.get("text")},
            )

        client = await gateway.connect(mock_websocket)

        await gateway.handle_message(
            client.client_id,
            {"type": "chat.message", "payload": {"text": "hello"}},
        )

        assert handler_called is True

    @pytest.mark.asyncio
    async def test_presence_list(self, gateway: Gateway) -> None:
        """Test getting presence information."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await gateway.connect(ws1, client_id="client-1")
        await gateway.connect(ws2, client_id="client-2")

        # Identify first client
        await gateway.handle_message(
            "client-1",
            {"type": "identify", "payload": {"user_id": "user-1", "device_type": "desktop"}},
        )

        presence = gateway.get_presence()

        assert len(presence) == 2
        # Find the identified client
        identified = next(p for p in presence if p["client_id"] == "client-1")
        assert identified["user_id"] == "user-1"
        assert identified["device_type"] == "desktop"
        assert identified["state"] == ConnectionState.READY.value


class TestGatewayEvent:
    """Tests for GatewayEvent model."""

    def test_create_event(self) -> None:
        """Test creating an event."""
        event = GatewayEvent(
            type=GatewayEventType.CHAT_MESSAGE,
            payload={"text": "hello"},
        )

        assert event.type == GatewayEventType.CHAT_MESSAGE
        assert event.payload["text"] == "hello"
        assert event.seq is None

    def test_event_with_sequence(self) -> None:
        """Test event with sequence number."""
        event = GatewayEvent(
            type=GatewayEventType.SYSTEM,
            payload={},
            seq=42,
        )

        assert event.seq == 42

    def test_event_serialization(self) -> None:
        """Test event JSON serialization."""
        event = GatewayEvent(
            type=GatewayEventType.CHAT_MESSAGE,
            payload={"text": "hello"},
            seq=1,
        )

        json_str = event.model_dump_json()
        assert "chat.message" in json_str
        assert "hello" in json_str


class TestGatewayClient:
    """Tests for GatewayClient dataclass."""

    def test_create_client(self) -> None:
        """Test creating a client."""
        ws = MagicMock()
        client = GatewayClient(
            client_id="test-123",
            websocket=ws,
        )

        assert client.client_id == "test-123"
        assert client.state == ConnectionState.CONNECTING
        assert client.user_id is None
        assert client.device_type == "unknown"

    def test_client_subscriptions(self) -> None:
        """Test client subscription management."""
        ws = MagicMock()
        client = GatewayClient(
            client_id="test-123",
            websocket=ws,
        )

        client.subscriptions.add("chat")
        client.subscriptions.add("recording")

        assert "chat" in client.subscriptions
        assert "recording" in client.subscriptions
        assert len(client.subscriptions) == 2
