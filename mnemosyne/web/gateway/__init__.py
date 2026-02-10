"""
WebSocket Gateway Protocol

A full-featured WebSocket gateway with:
- Event streaming with sequence numbers
- Presence tracking (who's connected)
- Gap detection and recovery
- Reconnection with exponential backoff
- Multi-client support
- Authentication

Inspired by openclaw's gateway protocol.
"""

from mnemosyne.web.gateway.gateway import (
    Gateway,
    GatewayClient,
    GatewayEvent,
    GatewayEventType,
    ConnectionState,
    get_gateway,
)

__all__ = [
    "Gateway",
    "GatewayClient",
    "GatewayEvent",
    "GatewayEventType",
    "ConnectionState",
    "get_gateway",
]
