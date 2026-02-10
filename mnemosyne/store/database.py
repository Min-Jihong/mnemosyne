import sqlite3
import threading
from pathlib import Path
from typing import Iterator

from mnemosyne.store.models import Session, StoredEvent, Screenshot


class Database:
    
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()
    
    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_schema(self) -> None:
        cursor = self._conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                started_at REAL,
                ended_at REAL,
                event_count INTEGER DEFAULT 0,
                screenshot_count INTEGER DEFAULT 0,
                platform TEXT,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp REAL,
                action_type TEXT,
                data TEXT,
                screenshot_id TEXT,
                window_app TEXT,
                window_title TEXT,
                inferred_intent TEXT,
                reasoning TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (screenshot_id) REFERENCES screenshots(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenshots (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp REAL,
                filepath TEXT,
                width INTEGER,
                height INTEGER,
                file_size INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_session 
            ON events(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp 
            ON events(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_screenshots_session 
            ON screenshots(session_id)
        """)
        
        self._conn.commit()
    
    def create_session(self, session: Session) -> None:
        cursor = self._conn.cursor()
        d = session.to_dict()
        cursor.execute("""
            INSERT INTO sessions (id, name, started_at, ended_at, event_count, 
                                  screenshot_count, platform, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (d["id"], d["name"], d["started_at"], d["ended_at"], 
              d["event_count"], d["screenshot_count"], d["platform"], d["metadata"]))
        self._conn.commit()
    
    def update_session(self, session: Session) -> None:
        cursor = self._conn.cursor()
        d = session.to_dict()
        cursor.execute("""
            UPDATE sessions SET
                name = ?,
                started_at = ?,
                ended_at = ?,
                event_count = ?,
                screenshot_count = ?,
                platform = ?,
                metadata = ?
            WHERE id = ?
        """, (d["name"], d["started_at"], d["ended_at"], d["event_count"],
              d["screenshot_count"], d["platform"], d["metadata"], d["id"]))
        self._conn.commit()
    
    def get_session(self, session_id: str) -> Session | None:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, name, started_at, ended_at, event_count, 
                   screenshot_count, platform, metadata
            FROM sessions WHERE id = ?
        """, (session_id,))
        row = cursor.fetchone()
        return Session.from_row(tuple(row)) if row else None
    
    def list_sessions(self, limit: int = 100) -> list[Session]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, name, started_at, ended_at, event_count,
                   screenshot_count, platform, metadata
            FROM sessions
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))
        return [Session.from_row(tuple(row)) for row in cursor.fetchall()]
    
    def insert_event(self, event: StoredEvent) -> None:
        cursor = self._conn.cursor()
        d = event.to_dict()
        cursor.execute("""
            INSERT INTO events (id, session_id, timestamp, action_type, data,
                               screenshot_id, window_app, window_title,
                               inferred_intent, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (d["id"], d["session_id"], d["timestamp"], d["action_type"],
              d["data"], d["screenshot_id"], d["window_app"], d["window_title"],
              d["inferred_intent"], d["reasoning"]))
        self._conn.commit()
    
    def insert_events_batch(self, events: list[StoredEvent]) -> None:
        cursor = self._conn.cursor()
        data = [
            (e.id, e.session_id, e.timestamp, e.action_type,
             e.to_dict()["data"], e.screenshot_id, e.window_app,
             e.window_title, e.inferred_intent, e.reasoning)
            for e in events
        ]
        cursor.executemany("""
            INSERT INTO events (id, session_id, timestamp, action_type, data,
                               screenshot_id, window_app, window_title,
                               inferred_intent, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        self._conn.commit()
    
    def get_events(
        self,
        session_id: str,
        action_types: list[str] | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 1000,
    ) -> list[StoredEvent]:
        cursor = self._conn.cursor()
        
        query = """
            SELECT id, session_id, timestamp, action_type, data,
                   screenshot_id, window_app, window_title,
                   inferred_intent, reasoning
            FROM events
            WHERE session_id = ?
        """
        params: list = [session_id]
        
        if action_types:
            placeholders = ",".join("?" * len(action_types))
            query += f" AND action_type IN ({placeholders})"
            params.extend(action_types)
        
        if start_time is not None:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time is not None:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [StoredEvent.from_row(tuple(row)) for row in cursor.fetchall()]
    
    def iter_events(
        self,
        session_id: str,
        batch_size: int = 100,
    ) -> Iterator[StoredEvent]:
        cursor = self._conn.cursor()
        offset = 0
        
        while True:
            cursor.execute("""
                SELECT id, session_id, timestamp, action_type, data,
                       screenshot_id, window_app, window_title,
                       inferred_intent, reasoning
                FROM events
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ? OFFSET ?
            """, (session_id, batch_size, offset))
            
            rows = cursor.fetchall()
            if not rows:
                break
            
            for row in rows:
                yield StoredEvent.from_row(tuple(row))
            
            offset += batch_size
    
    def insert_screenshot(self, screenshot: Screenshot) -> None:
        cursor = self._conn.cursor()
        d = screenshot.to_dict()
        cursor.execute("""
            INSERT INTO screenshots (id, session_id, timestamp, filepath,
                                    width, height, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (d["id"], d["session_id"], d["timestamp"], d["filepath"],
              d["width"], d["height"], d["file_size"]))
        self._conn.commit()
    
    def get_screenshot(self, screenshot_id: str) -> Screenshot | None:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, session_id, timestamp, filepath, width, height, file_size
            FROM screenshots WHERE id = ?
        """, (screenshot_id,))
        row = cursor.fetchone()
        return Screenshot.from_row(tuple(row)) if row else None
    
    def get_screenshots_for_session(
        self,
        session_id: str,
        limit: int = 1000,
    ) -> list[Screenshot]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, session_id, timestamp, filepath, width, height, file_size
            FROM screenshots
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (session_id, limit))
        return [Screenshot.from_row(tuple(row)) for row in cursor.fetchall()]
    
    def update_event_intent(
        self,
        event_id: str,
        inferred_intent: str,
        reasoning: str | None = None,
    ) -> None:
        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE events SET inferred_intent = ?, reasoning = ?
            WHERE id = ?
        """, (inferred_intent, reasoning, event_id))
        self._conn.commit()
    
    def get_events_without_intent(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[StoredEvent]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, session_id, timestamp, action_type, data,
                   screenshot_id, window_app, window_title,
                   inferred_intent, reasoning
            FROM events
            WHERE session_id = ? AND inferred_intent IS NULL
            ORDER BY timestamp ASC
            LIMIT ?
        """, (session_id, limit))
        return [StoredEvent.from_row(tuple(row)) for row in cursor.fetchall()]
    
    def close(self) -> None:
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            del self._local.conn
