import pytest
from mnemosyne.store.database import Database
from mnemosyne.store.models import Session, StoredEvent, Screenshot


class TestDatabase:
    
    def test_create_database(self, temp_dir):
        db = Database(temp_dir / "test.db")
        assert (temp_dir / "test.db").exists()
        db.close()
    
    def test_create_session(self, temp_dir):
        db = Database(temp_dir / "test.db")
        
        session = Session(
            name="Test Session",
            started_at=1000.0,
            platform="darwin",
        )
        
        db.create_session(session)
        
        retrieved = db.get_session(session.id)
        assert retrieved is not None
        assert retrieved.name == "Test Session"
        assert retrieved.platform == "darwin"
        
        db.close()
    
    def test_list_sessions(self, temp_dir):
        db = Database(temp_dir / "test.db")
        
        for i in range(5):
            session = Session(name=f"Session {i}", started_at=1000.0 + i)
            db.create_session(session)
        
        sessions = db.list_sessions(limit=3)
        assert len(sessions) == 3
        
        db.close()
    
    def test_insert_event(self, temp_dir):
        db = Database(temp_dir / "test.db")
        
        session = Session(name="Test", started_at=1000.0)
        db.create_session(session)
        
        event = StoredEvent(
            session_id=session.id,
            timestamp=1001.0,
            action_type="mouse_click",
            data={"x": 100, "y": 200},
            window_app="Safari",
        )
        
        db.insert_event(event)
        
        events = db.get_events(session.id)
        assert len(events) == 1
        assert events[0].action_type == "mouse_click"
        assert events[0].data["x"] == 100
        
        db.close()
    
    def test_batch_insert_events(self, temp_dir):
        db = Database(temp_dir / "test.db")
        
        session = Session(name="Test", started_at=1000.0)
        db.create_session(session)
        
        events = [
            StoredEvent(
                session_id=session.id,
                timestamp=1000.0 + i,
                action_type="key_press",
                data={"key": chr(97 + i)},
            )
            for i in range(10)
        ]
        
        db.insert_events_batch(events)
        
        retrieved = db.get_events(session.id)
        assert len(retrieved) == 10
        
        db.close()
    
    def test_insert_screenshot(self, temp_dir):
        db = Database(temp_dir / "test.db")
        
        session = Session(name="Test", started_at=1000.0)
        db.create_session(session)
        
        screenshot = Screenshot(
            session_id=session.id,
            timestamp=1001.0,
            filepath="/path/to/screenshot.png",
            width=1920,
            height=1080,
            file_size=50000,
        )
        
        db.insert_screenshot(screenshot)
        
        retrieved = db.get_screenshot(screenshot.id)
        assert retrieved is not None
        assert retrieved.width == 1920
        assert retrieved.filepath == "/path/to/screenshot.png"
        
        db.close()
    
    def test_update_event_intent(self, temp_dir):
        db = Database(temp_dir / "test.db")
        
        session = Session(name="Test", started_at=1000.0)
        db.create_session(session)
        
        event = StoredEvent(
            session_id=session.id,
            timestamp=1001.0,
            action_type="mouse_click",
        )
        db.insert_event(event)
        
        db.update_event_intent(
            event_id=event.id,
            inferred_intent="User clicked to submit form",
            reasoning="Button labeled 'Submit' was clicked",
        )
        
        events = db.get_events(session.id)
        assert events[0].inferred_intent == "User clicked to submit form"
        
        db.close()
