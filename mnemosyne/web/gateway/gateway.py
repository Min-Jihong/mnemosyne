"""Gateway protocol implementation."""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Coroutine

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GatewayEventType(str, Enum):
    """Types of gateway events."""

    # Connection events
    HELLO = "hello"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    IDENTIFY = "identify"
    READY = "ready"
    RECONNECT = "reconnect"
    DISCONNECT = "disconnect"

    # Application events
    CHAT_MESSAGE = "chat.message"
    CHAT_STREAM_START = "chat.stream_start"
    CHAT_STREAM_CHUNK = "chat.stream_chunk"
    CHAT_STREAM_END = "chat.stream_end"

    RECORDING_START = "recording.start"
    RECORDING_STOP = "recording.stop"
    RECORDING_EVENT = "recording.event"

    MEMORY_STORE = "memory.store"
    MEMORY_RETRIEVE = "memory.retrieve"

    PRESENCE_UPDATE = "presence.update"
    PRESENCE_JOIN = "presence.join"
    PRESENCE_LEAVE = "presence.leave"

    ERROR = "error"
    SYSTEM = "system"


class ConnectionState(str, Enum):
    """WebSocket connection states."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    IDENTIFYING = "identifying"
    READY = "ready"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"


class GatewayEvent(BaseModel):
    """A gateway event message."""

    type: GatewayEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    seq: int | None = None  # Sequence number for event ordering
    timestamp: datetime = Field(default_factory=datetime.now)
    client_id: str | None = None  # Source client ID


class GatewayError(BaseModel):
    """A gateway error."""

    code: int
    message: str
    recoverable: bool = True


@dataclass
class GatewayClient:
    """Represents a connected client."""

    client_id: str
    websocket: Any  # WebSocket connection
    state: ConnectionState = ConnectionState.CONNECTING
    user_id: str | None = None
    device_type: str = "unknown"
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    subscriptions: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Sequence tracking
    last_seq_sent: int = 0
    last_seq_received: int = 0


class Gateway:
    """
    WebSocket Gateway for real-time communication.

    Features:
    - Multi-client support with presence tracking
    - Event streaming with sequence numbers
    - Gap detection for missed events
    - Heartbeat monitoring
    - Automatic reconnection support
    - Event subscriptions
    """

    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        heartbeat_timeout: float = 90.0,
    ) -> None:
        self._clients: dict[str, GatewayClient] = {}
        self._sequence: int = 0
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_timeout = heartbeat_timeout
        self._event_handlers: dict[GatewayEventType, list[Callable]] = {}
        self._running = False
        self._heartbeat_task: asyncio.Task | None = None

        # Event history for gap recovery (last N events)
        self._event_history: list[GatewayEvent] = []
        self._history_max_size = 1000

    @property
    def clients(self) -> dict[str, GatewayClient]:
        """Get all connected clients."""
        return self._clients.copy()

    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)

    def _next_seq(self) -> int:
        """Get next sequence number."""
        self._sequence += 1
        return self._sequence

    async def connect(self, websocket: Any, client_id: str | None = None) -> GatewayClient:
        """
        Handle a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            client_id: Optional client ID (generated if not provided)

        Returns:
            The new GatewayClient
        """
        client_id = client_id or str(uuid.uuid4())

        client = GatewayClient(
            client_id=client_id,
            websocket=websocket,
        )
        self._clients[client_id] = client

        # Send HELLO event
        hello_event = GatewayEvent(
            type=GatewayEventType.HELLO,
            payload={
                "heartbeat_interval": self._heartbeat_interval,
                "client_id": client_id,
            },
        )
        await self._send_to_client(client, hello_event)

        logger.info(f"Client connected: {client_id}")
        return client

    async def disconnect(self, client_id: str, reason: str = "unknown") -> None:
        """
        Handle client disconnection.

        Args:
            client_id: The client to disconnect
            reason: Reason for disconnection
        """
        client = self._clients.pop(client_id, None)
        if client is None:
            return

        client.state = ConnectionState.DISCONNECTED

        # Notify other clients
        await self.broadcast(
            GatewayEventType.PRESENCE_LEAVE,
            {
                "client_id": client_id,
                "user_id": client.user_id,
                "reason": reason,
            },
            exclude=[client_id],
        )

        logger.info(f"Client disconnected: {client_id} ({reason})")

    async def handle_message(
        self,
        client_id: str,
        message: str | dict,
    ) -> GatewayEvent | None:
        """
        Handle an incoming message from a client.

        Args:
            client_id: The source client
            message: The message (JSON string or dict)

        Returns:
            Response event or None
        """
        client = self._clients.get(client_id)
        if client is None:
            return None

        # Parse message
        if isinstance(message, str):
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                return self._error_event(4001, "Invalid JSON")
        else:
            data = message

        # Parse event
        try:
            event = GatewayEvent(**data)
        except Exception as e:
            return self._error_event(4002, f"Invalid event format: {e}")

        # Update sequence tracking
        if event.seq is not None:
            # Check for gap
            expected_seq = client.last_seq_received + 1
            if event.seq > expected_seq:
                logger.warning(
                    f"Gap detected for {client_id}: expected {expected_seq}, got {event.seq}"
                )
                # Could trigger gap recovery here

            client.last_seq_received = event.seq

        # Handle event by type
        handler = getattr(self, f"_handle_{event.type.value.replace('.', '_')}", None)
        if handler:
            return await handler(client, event)

        # Dispatch to registered handlers
        return await self._dispatch_event(client, event)

    async def _handle_heartbeat(
        self,
        client: GatewayClient,
        event: GatewayEvent,
    ) -> GatewayEvent:
        """Handle heartbeat from client."""
        client.last_heartbeat = datetime.now()
        return GatewayEvent(
            type=GatewayEventType.HEARTBEAT_ACK,
            payload={"timestamp": time.time()},
        )

    async def _handle_identify(
        self,
        client: GatewayClient,
        event: GatewayEvent,
    ) -> GatewayEvent:
        """Handle client identification."""
        payload = event.payload

        client.user_id = payload.get("user_id")
        client.device_type = payload.get("device_type", "unknown")
        client.metadata = payload.get("metadata", {})
        client.state = ConnectionState.READY

        # Notify other clients
        await self.broadcast(
            GatewayEventType.PRESENCE_JOIN,
            {
                "client_id": client.client_id,
                "user_id": client.user_id,
                "device_type": client.device_type,
            },
            exclude=[client.client_id],
        )

        # Send presence list to new client
        presence_list = [
            {
                "client_id": c.client_id,
                "user_id": c.user_id,
                "device_type": c.device_type,
                "state": c.state.value,
            }
            for c in self._clients.values()
            if c.state == ConnectionState.READY
        ]

        return GatewayEvent(
            type=GatewayEventType.READY,
            payload={
                "client_id": client.client_id,
                "presence": presence_list,
                "last_seq": self._sequence,
            },
        )

    async def _dispatch_event(
        self,
        client: GatewayClient,
        event: GatewayEvent,
    ) -> GatewayEvent | None:
        """Dispatch event to registered handlers."""
        handlers = self._event_handlers.get(event.type, [])

        for handler in handlers:
            try:
                result = await handler(client, event)
                if result is not None:
                    return result
            except Exception as e:
                logger.error(f"Event handler error: {e}")

        return None

    def on_event(
        self,
        event_type: GatewayEventType,
    ) -> Callable:
        """Decorator to register an event handler."""

        def decorator(handler: Callable) -> Callable:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)
            return handler

        return decorator

    async def send(
        self,
        client_id: str,
        event_type: GatewayEventType,
        payload: dict[str, Any],
    ) -> bool:
        """
        Send an event to a specific client.

        Args:
            client_id: Target client
            event_type: Event type
            payload: Event data

        Returns:
            True if sent successfully
        """
        client = self._clients.get(client_id)
        if client is None:
            return False

        event = GatewayEvent(
            type=event_type,
            payload=payload,
            seq=self._next_seq(),
        )
        return await self._send_to_client(client, event)

    async def broadcast(
        self,
        event_type: GatewayEventType,
        payload: dict[str, Any],
        *,
        exclude: list[str] | None = None,
        only: list[str] | None = None,
    ) -> int:
        """
        Broadcast an event to multiple clients.

        Args:
            event_type: Event type
            payload: Event data
            exclude: Client IDs to exclude
            only: Only send to these client IDs

        Returns:
            Number of clients sent to
        """
        exclude = exclude or []
        seq = self._next_seq()

        event = GatewayEvent(
            type=event_type,
            payload=payload,
            seq=seq,
        )

        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._history_max_size:
            self._event_history.pop(0)

        sent_count = 0
        targets = self._clients.values()

        if only:
            targets = [c for c in targets if c.client_id in only]

        for client in targets:
            if client.client_id in exclude:
                continue
            if client.state != ConnectionState.READY:
                continue

            if await self._send_to_client(client, event):
                sent_count += 1

        return sent_count

    async def _send_to_client(
        self,
        client: GatewayClient,
        event: GatewayEvent,
    ) -> bool:
        """Send an event to a client."""
        try:
            message = event.model_dump_json()
            await client.websocket.send_text(message)

            if event.seq is not None:
                client.last_seq_sent = event.seq

            return True
        except Exception as e:
            logger.error(f"Failed to send to {client.client_id}: {e}")
            return False

    def _error_event(self, code: int, message: str) -> GatewayEvent:
        """Create an error event."""
        return GatewayEvent(
            type=GatewayEventType.ERROR,
            payload={
                "code": code,
                "message": message,
            },
        )

    async def get_events_since(self, seq: int) -> list[GatewayEvent]:
        """
        Get events since a sequence number (for gap recovery).

        Args:
            seq: Last received sequence number

        Returns:
            List of events after that sequence
        """
        return [e for e in self._event_history if e.seq and e.seq > seq]

    async def start_heartbeat_monitor(self) -> None:
        """Start the heartbeat monitoring task."""
        if self._running:
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop_heartbeat_monitor(self) -> None:
        """Stop the heartbeat monitoring task."""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _heartbeat_loop(self) -> None:
        """Monitor client heartbeats."""
        while self._running:
            await asyncio.sleep(self._heartbeat_interval)

            now = datetime.now()
            disconnected = []

            for client_id, client in self._clients.items():
                elapsed = (now - client.last_heartbeat).total_seconds()

                if elapsed > self._heartbeat_timeout:
                    disconnected.append(client_id)
                    logger.warning(f"Client {client_id} heartbeat timeout")

            for client_id in disconnected:
                await self.disconnect(client_id, "heartbeat_timeout")

    def get_presence(self) -> list[dict[str, Any]]:
        """Get presence information for all connected clients."""
        return [
            {
                "client_id": c.client_id,
                "user_id": c.user_id,
                "device_type": c.device_type,
                "state": c.state.value,
                "connected_at": c.connected_at.isoformat(),
                "last_heartbeat": c.last_heartbeat.isoformat(),
            }
            for c in self._clients.values()
        ]


# Global gateway instance
_gateway: Gateway | None = None


def get_gateway() -> Gateway:
    """Get or create the global gateway."""
    global _gateway
    if _gateway is None:
        _gateway = Gateway()
    return _gateway
