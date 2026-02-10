#!/usr/bin/env python3
"""
Basic Recording Example

This example demonstrates how to start a recording session programmatically
and capture your computer activity (mouse, keyboard, screen).

Usage:
    python basic_recording.py

Requirements:
    - macOS with Accessibility permissions granted
    - pip install mnemosyne[macos]
"""

import asyncio
import signal
import sys
from datetime import datetime

# Add parent directory to path for development
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from mnemosyne.capture.events import EventType
from mnemosyne.capture.mouse import MouseCapture
from mnemosyne.capture.keyboard import KeyboardCapture
from mnemosyne.capture.screen import ScreenCapture
from mnemosyne.capture.window import WindowCapture
from mnemosyne.store.database import Database


class RecordingSession:
    """A simple recording session that captures all input events."""

    def __init__(self, session_name: str = "example_session"):
        self.session_name = session_name
        self.db = Database()
        self.session_id: str | None = None
        self.running = False

        # Capture components
        self.mouse_capture = MouseCapture()
        self.keyboard_capture = KeyboardCapture()
        self.screen_capture = ScreenCapture()
        self.window_capture = WindowCapture()

        # Event counters
        self.event_counts = {
            "mouse_move": 0,
            "mouse_click": 0,
            "key_press": 0,
            "screenshot": 0,
            "window_change": 0,
        }

    async def start(self):
        """Start the recording session."""
        print(f"🎬 Starting recording session: {self.session_name}")
        print("=" * 50)

        # Create session in database
        self.session_id = await self.db.create_session(
            name=self.session_name,
            metadata={"started_at": datetime.now().isoformat()},
        )
        print(f"📁 Session ID: {self.session_id}")

        # Register event handlers
        self._register_handlers()

        # Start all capture components
        self.running = True
        await asyncio.gather(
            self.mouse_capture.start(),
            self.keyboard_capture.start(),
            self.window_capture.start(),
        )

    def _register_handlers(self):
        """Register event handlers for each capture component."""

        @self.mouse_capture.on_event
        async def handle_mouse(event):
            if event.type == EventType.MOUSE_MOVE:
                self.event_counts["mouse_move"] += 1
                # Only log every 100th move event to reduce noise
                if self.event_counts["mouse_move"] % 100 == 0:
                    print(f"🖱️  Mouse position: ({event.x}, {event.y})")
            elif event.type in (EventType.MOUSE_CLICK, EventType.MOUSE_DOUBLE_CLICK):
                self.event_counts["mouse_click"] += 1
                print(f"🖱️  Click at ({event.x}, {event.y}) - {event.button}")
                # Capture screenshot on click
                await self._capture_screenshot("click")

            # Save to database
            if self.session_id:
                await self.db.save_event(self.session_id, event)

        @self.keyboard_capture.on_event
        async def handle_keyboard(event):
            self.event_counts["key_press"] += 1
            # Don't log actual keys for privacy, just count
            if self.event_counts["key_press"] % 10 == 0:
                print(f"⌨️  Key events: {self.event_counts['key_press']}")

            if self.session_id:
                await self.db.save_event(self.session_id, event)

        @self.window_capture.on_event
        async def handle_window(event):
            self.event_counts["window_change"] += 1
            print(f"🪟 Window: {event.app_name} - {event.title[:50]}...")

            if self.session_id:
                await self.db.save_event(self.session_id, event)

    async def _capture_screenshot(self, trigger: str):
        """Capture a screenshot."""
        try:
            screenshot = await self.screen_capture.capture()
            self.event_counts["screenshot"] += 1

            if self.session_id and screenshot:
                await self.db.save_screenshot(
                    self.session_id, screenshot, metadata={"trigger": trigger}
                )
                print(f"📸 Screenshot captured ({trigger})")
        except Exception as e:
            print(f"⚠️  Screenshot failed: {e}")

    async def stop(self):
        """Stop the recording session."""
        print("\n" + "=" * 50)
        print("🛑 Stopping recording session...")

        self.running = False

        # Stop all capture components
        await self.mouse_capture.stop()
        await self.keyboard_capture.stop()
        await self.window_capture.stop()

        # Print summary
        print("\n📊 Session Summary:")
        print(f"   Mouse moves: {self.event_counts['mouse_move']}")
        print(f"   Mouse clicks: {self.event_counts['mouse_click']}")
        print(f"   Key presses: {self.event_counts['key_press']}")
        print(f"   Window changes: {self.event_counts['window_change']}")
        print(f"   Screenshots: {self.event_counts['screenshot']}")

        # Close database
        await self.db.close()
        print(f"\n✅ Session saved: {self.session_id}")


async def main():
    """Main entry point."""
    session = RecordingSession(
        session_name=f"example_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    # Handle Ctrl+C gracefully
    loop = asyncio.get_event_loop()

    def signal_handler():
        print("\n\n⚠️  Received interrupt signal...")
        asyncio.create_task(session.stop())
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    print("🚀 Mnemosyne Recording Example")
    print("Press Ctrl+C to stop recording\n")

    try:
        await session.start()
        # Keep running until interrupted
        while session.running:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if session.running:
            await session.stop()


if __name__ == "__main__":
    asyncio.run(main())
