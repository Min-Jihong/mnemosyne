#!/usr/bin/env python3
"""
Web API Client Example

This example demonstrates how to interact with Mnemosyne's web API
programmatically using Python requests.

Usage:
    # First, start the web server in another terminal:
    mnemosyne web

    # Then run this script:
    python web_api_client.py

Requirements:
    - pip install requests
    - Mnemosyne web server running (mnemosyne web)
"""

import requests
import json
import time
from typing import Any

# API base URL
BASE_URL = "http://localhost:8000"


class MnemosyneClient:
    """A simple client for the Mnemosyne REST API."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def health_check(self) -> dict:
        """Check if the server is running."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def configure_llm(
        self, provider: str, api_key: str, model: str | None = None
    ) -> dict:
        """Configure the LLM provider."""
        payload = {
            "provider": provider,
            "api_key": api_key,
        }
        if model:
            payload["model"] = model

        response = self.session.post(f"{self.base_url}/api/config/llm", json=payload)
        response.raise_for_status()
        return response.json()

    def chat(self, message: str, conversation_id: str | None = None) -> dict:
        """Send a chat message to your digital twin."""
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = self.session.post(f"{self.base_url}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()

    def get_conversations(self) -> list:
        """Get all conversations."""
        response = self.session.get(f"{self.base_url}/api/conversations")
        response.raise_for_status()
        return response.json()

    def search_memories(self, query: str, limit: int = 10) -> list:
        """Search memories semantically."""
        response = self.session.get(
            f"{self.base_url}/api/memories/search",
            params={"q": query, "limit": limit},
        )
        response.raise_for_status()
        return response.json()

    def get_sessions(self) -> list:
        """Get all recording sessions."""
        response = self.session.get(f"{self.base_url}/api/sessions")
        response.raise_for_status()
        return response.json()

    def start_recording(self, name: str | None = None) -> dict:
        """Start a new recording session."""
        payload = {}
        if name:
            payload["name"] = name

        response = self.session.post(f"{self.base_url}/api/recording/start", json=payload)
        response.raise_for_status()
        return response.json()

    def stop_recording(self) -> dict:
        """Stop the current recording session."""
        response = self.session.post(f"{self.base_url}/api/recording/stop")
        response.raise_for_status()
        return response.json()

    def get_recording_status(self) -> dict:
        """Get current recording status."""
        response = self.session.get(f"{self.base_url}/api/recording/status")
        response.raise_for_status()
        return response.json()


def main():
    """Demonstrate API usage."""
    print("🧠 Mnemosyne Web API Client Example")
    print("=" * 50)

    client = MnemosyneClient()

    # Check server health
    print("\n1️⃣  Health Check")
    print("-" * 30)
    try:
        health = client.health_check()
        print(f"✅ Server status: {health.get('status', 'unknown')}")
        print(f"   Version: {health.get('version', 'unknown')}")
    except requests.ConnectionError:
        print("❌ Cannot connect to server!")
        print("💡 Start the server with: mnemosyne web")
        return

    # Configure LLM (example - you'd use your own API key)
    print("\n2️⃣  Configure LLM (example)")
    print("-" * 30)
    print("To configure LLM, call:")
    print('   client.configure_llm("anthropic", "your-api-key", "claude-3-opus")')
    print("   (Not running - would require real API key)")

    # List sessions
    print("\n3️⃣  Recording Sessions")
    print("-" * 30)
    try:
        sessions = client.get_sessions()
        if sessions:
            print(f"📋 Found {len(sessions)} sessions:")
            for s in sessions[:5]:
                print(f"   • {s.get('name', 'Unnamed')} ({s.get('id', '')[:8]}...)")
        else:
            print("📭 No sessions found")
    except Exception as e:
        print(f"⚠️  Could not fetch sessions: {e}")

    # Check recording status
    print("\n4️⃣  Recording Status")
    print("-" * 30)
    try:
        status = client.get_recording_status()
        is_recording = status.get("recording", False)
        print(f"🎬 Recording: {'Yes' if is_recording else 'No'}")
        if is_recording:
            print(f"   Session: {status.get('session_name', 'Unknown')}")
            print(f"   Events: {status.get('event_count', 0)}")
    except Exception as e:
        print(f"⚠️  Could not get status: {e}")

    # Search memories
    print("\n5️⃣  Memory Search")
    print("-" * 30)
    try:
        memories = client.search_memories("morning routine", limit=5)
        if memories:
            print(f"🔍 Found {len(memories)} matching memories:")
            for m in memories:
                print(f"   • {m.get('content', '')[:60]}...")
        else:
            print("📭 No memories found for 'morning routine'")
    except Exception as e:
        print(f"⚠️  Could not search memories: {e}")

    # Chat example
    print("\n6️⃣  Chat with Digital Twin")
    print("-" * 30)
    print("To chat, call:")
    print('   response = client.chat("What did I do yesterday?")')
    print("   (Requires configured LLM)")

    # API reference
    print("\n" + "=" * 50)
    print("📚 API Reference")
    print("=" * 50)
    print("""
Endpoints:
  GET  /health                    - Server health check
  POST /api/config/llm            - Configure LLM provider
  POST /api/chat                  - Chat with digital twin
  GET  /api/conversations         - List conversations
  GET  /api/memories/search       - Search memories
  GET  /api/sessions              - List recording sessions
  POST /api/recording/start       - Start recording
  POST /api/recording/stop        - Stop recording
  GET  /api/recording/status      - Get recording status

For full API documentation, visit: http://localhost:8000/docs
""")


if __name__ == "__main__":
    main()
