import sys
import time
from pathlib import Path
from queue import Queue
from threading import Thread, Event as ThreadEvent
from typing import Callable

from mnemosyne.store.database import Database
from mnemosyne.store.models import Session, StoredEvent, Screenshot
from mnemosyne.capture.events import Event, ScreenshotEvent, WindowChangeEvent
from mnemosyne.capture.recorder import Recorder, RecorderConfig, RecordingSession


class SessionManager:
    
    def __init__(
        self,
        data_dir: Path | str,
        recorder_config: RecorderConfig | None = None,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._db = Database(self.data_dir / "mnemosyne.db")
        self._recorder_config = recorder_config or RecorderConfig(
            output_dir=self.data_dir / "screenshots"
        )
        self._recorder: Recorder | None = None
        
        self._current_session: Session | None = None
        self._event_queue: Queue[Event] = Queue()
        self._stop_event = ThreadEvent()
        self._writer_thread: Thread | None = None
        
        self._current_window_app = ""
        self._current_window_title = ""
        self._last_screenshot_id: str | None = None
    
    def start_session(self, name: str = "") -> Session:
        if self._current_session is not None:
            raise RuntimeError("Session already active. Stop it first.")
        
        session = Session(
            name=name or f"Session {time.strftime('%Y-%m-%d %H:%M:%S')}",
            started_at=time.time(),
            platform=sys.platform,
        )
        
        self._db.create_session(session)
        self._current_session = session
        
        self._stop_event.clear()
        self._writer_thread = Thread(target=self._event_writer_loop, daemon=True)
        self._writer_thread.start()
        
        self._recorder = Recorder(
            config=self._recorder_config,
            on_event=self._on_event,
        )
        self._recorder.start(session_id=session.id)
        
        return session
    
    def stop_session(self) -> Session | None:
        if self._current_session is None:
            return None
        
        if self._recorder:
            self._recorder.stop()
            self._recorder = None
        
        self._stop_event.set()
        if self._writer_thread:
            self._writer_thread.join(timeout=5.0)
            self._writer_thread = None
        
        self._current_session.ended_at = time.time()
        self._db.update_session(self._current_session)
        
        session = self._current_session
        self._current_session = None
        
        return session
    
    def _on_event(self, event: Event) -> None:
        if isinstance(event, WindowChangeEvent):
            self._current_window_app = event.app_name
            self._current_window_title = event.window_title
        
        if isinstance(event, ScreenshotEvent):
            screenshot = Screenshot(
                session_id=self._current_session.id if self._current_session else "",
                timestamp=event.timestamp,
                filepath=event.filepath,
                width=event.width,
                height=event.height,
                file_size=event.file_size,
            )
            self._db.insert_screenshot(screenshot)
            self._last_screenshot_id = screenshot.id
            
            if self._current_session:
                self._current_session.screenshot_count += 1
        
        self._event_queue.put(event)
    
    def _event_writer_loop(self) -> None:
        batch: list[StoredEvent] = []
        batch_size = 50
        flush_interval = 1.0
        last_flush = time.time()
        
        while not self._stop_event.is_set():
            try:
                event = self._event_queue.get(timeout=0.1)
                
                if isinstance(event, ScreenshotEvent):
                    continue
                
                stored = StoredEvent(
                    session_id=self._current_session.id if self._current_session else "",
                    timestamp=event.timestamp,
                    action_type=event.action_type.value,
                    data=event.to_dict(),
                    screenshot_id=self._last_screenshot_id,
                    window_app=self._current_window_app,
                    window_title=self._current_window_title,
                )
                batch.append(stored)
                
                if self._current_session:
                    self._current_session.event_count += 1
                
                current_time = time.time()
                if len(batch) >= batch_size or (current_time - last_flush) >= flush_interval:
                    if batch:
                        self._db.insert_events_batch(batch)
                        batch = []
                        last_flush = current_time
                        
            except Exception:
                pass
        
        if batch:
            self._db.insert_events_batch(batch)
    
    def get_current_session(self) -> Session | None:
        return self._current_session
    
    def list_sessions(self, limit: int = 100) -> list[Session]:
        return self._db.list_sessions(limit)
    
    def get_session(self, session_id: str) -> Session | None:
        return self._db.get_session(session_id)
    
    def get_events(
        self,
        session_id: str,
        action_types: list[str] | None = None,
        limit: int = 1000,
    ) -> list[StoredEvent]:
        return self._db.get_events(
            session_id=session_id,
            action_types=action_types,
            limit=limit,
        )
    
    def get_screenshots(
        self,
        session_id: str,
        limit: int = 1000,
    ) -> list[Screenshot]:
        return self._db.get_screenshots_for_session(session_id, limit)
    
    @property
    def database(self) -> Database:
        return self._db
