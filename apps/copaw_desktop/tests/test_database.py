"""Unit tests for session database operations."""

import pytest
from datetime import datetime
from typing import Dict, List
from unittest.mock import patch

from copaw_desktop.core.database import SessionDB, SessionModel, MessageModel


class TestSessionDBInit:
    """Tests for SessionDB initialization."""
    
    def test_init_memory_db(self):
        """Test initialization with in-memory database."""
        db = SessionDB(":memory:")
        
        assert db.db_path == ":memory:"
        assert db.engine is not None
    
    def test_init_file_db(self, temp_db_path):
        """Test initialization with file database."""
        db = SessionDB(temp_db_path)
        
        assert db.db_path == temp_db_path
        assert db.engine is not None


class TestSessionDBCreateSession:
    """Tests for create_session method."""
    
    def test_create_session_basic(self):
        """Test basic session creation."""
        db = SessionDB(":memory:")
        
        session_id = db.create_session()
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID format
    
    def test_create_session_with_title(self):
        """Test session creation with title."""
        db = SessionDB(":memory:")
        
        title = "My Chat Session"
        session_id = db.create_session(title=title)
        
        # Verify session was created
        with db.SessionLocal() as session:
            session_obj = session.query(SessionModel).filter_by(id=session_id).first()
            
            assert session_obj is not None
            assert session_obj.title == title
    
    def test_create_multiple_sessions(self):
        """Test creating multiple sessions."""
        db = SessionDB(":memory:")
        
        id1 = db.create_session("Session 1")
        id2 = db.create_session("Session 2")
        id3 = db.create_session("Session 3")
        
        with db.SessionLocal() as session:
            count = session.query(SessionModel).count()
            assert count == 3


class TestSessionDBAddMessage:
    """Tests for add_message method."""
    
    def test_add_message_user(self):
        """Test adding user message."""
        db = SessionDB(":memory:")
        
        session_id = db.create_session()
        message_id = db.add_message(
            session_id=session_id,
            role="user",
            content="Hello, CoPaw!",
        )
        
        assert message_id is not None
        assert len(message_id) == 36
    
    def test_add_message_assistant(self):
        """Test adding assistant message."""
        db = SessionDB(":memory:")
        
        session_id = db.create_session()
        message_id = db.add_message(
            session_id=session_id,
            role="assistant",
            content="Hi! How can I help you?",
        )
        
        assert message_id is not None
    
    def test_add_message_with_widget(self):
        """Test adding message with widget data."""
        db = SessionDB(":memory:")
        
        session_id = db.create_session()
        widget_data = {
            "type": "chart",
            "data": {"x": [1, 2, 3], "y": [4, 5, 6]},
        }
        
        message_id = db.add_message(
            session_id=session_id,
            role="assistant",
            content="Here's the chart you requested.",
            widget_data=widget_data,
        )
        
        assert message_id is not None
        
        # Verify widget data was saved
        with db.SessionLocal() as session:
            msg = session.query(MessageModel).filter_by(id=message_id).first()
            assert msg.widget_data == widget_data


class TestSessionDBGetMessages:
    """Tests for get_messages method."""
    
    def test_get_messages_empty_session(self):
        """Test getting messages from empty session."""
        db = SessionDB(":memory:")
        
        session_id = db.create_session()
        messages = db.get_messages(session_id)
        
        assert messages == []
    
    def test_get_messages_multiple(self):
        """Test getting multiple messages."""
        db = SessionDB(":memory:")
        
        session_id = db.create_session()
        
        db.add_message(session_id, "user", "Message 1")
        db.add_message(session_id, "assistant", "Response 1")
        db.add_message(session_id, "user", "Message 2")
        
        messages = db.get_messages(session_id)
        
        assert len(messages) == 3
        assert messages[0]["content"] == "Message 1"
        assert messages[1]["content"] == "Response 1"
        assert messages[2]["content"] == "Message 2"
    
    def test_get_messages_ordered_by_time(self):
        """Test that messages are ordered by creation time."""
        db = SessionDB(":memory:")
        
        session_id = db.create_session()
        
        # Add messages with small delays
        import time
        db.add_message(session_id, "user", "First")
        time.sleep(0.01)
        db.add_message(session_id, "assistant", "Second")
        time.sleep(0.01)
        db.add_message(session_id, "user", "Third")
        
        messages = db.get_messages(session_id)
        
        assert messages[0]["content"] == "First"
        assert messages[1]["content"] == "Second"
        assert messages[2]["content"] == "Third"


class TestSessionDBGroupByHour:
    """Tests for get_sessions_grouped_by_hour method."""
    
    def test_group_by_hour_empty_db(self):
        """Test grouping with no sessions."""
        db = SessionDB(":memory:")
        
        grouped = db.get_sessions_grouped_by_hour()
        
        assert grouped == {}
    
    def test_group_by_hour_single_session(self):
        """Test grouping with single session."""
        db = SessionDB(":memory:")
        
        session_id = db.create_session("Test Session")
        
        grouped = db.get_sessions_grouped_by_hour()
        
        # Should have one date
        assert len(grouped) == 1
        date_key = list(grouped.keys())[0]
        
        # Should have one hour
        hour_dict = grouped[date_key]
        assert len(hour_dict) == 1
        hour_key = list(hour_dict.keys())[0]
        
        # Should have one session
        sessions = hour_dict[hour_key]
        assert len(sessions) == 1
        assert sessions[0]["id"] == session_id
    
    def test_group_by_hour_multiple_sessions(self):
        """Test grouping with multiple sessions."""
        db = SessionDB(":memory:")
        
        # Create sessions (all will be in current hour)
        id1 = db.create_session("Session 1")
        id2 = db.create_session("Session 2")
        id3 = db.create_session("Session 3")
        
        grouped = db.get_sessions_grouped_by_hour()
        
        # Should have one date
        assert len(grouped) == 1
        date_key = list(grouped.keys())[0]
        
        # Should have one hour
        hour_dict = grouped[date_key]
        assert len(hour_dict) == 1
        hour_key = list(hour_dict.keys())[0]
        
        # Should have 3 sessions
        sessions = hour_dict[hour_key]
        assert len(sessions) == 3
        
        session_ids = [s["id"] for s in sessions]
        assert id1 in session_ids
        assert id2 in session_ids
        assert id3 in session_ids
    
    def test_group_by_hour_returns_required_fields(self):
        """Test that grouped sessions have all required fields."""
        db = SessionDB(":memory:")
        
        title = "Test Session"
        session_id = db.create_session(title)
        
        grouped = db.get_sessions_grouped_by_hour()
        
        date_key = list(grouped.keys())[0]
        hour_dict = grouped[date_key]
        hour_key = list(hour_dict.keys())[0]
        sessions = hour_dict[hour_key]
        
        session = sessions[0]
        assert session["id"] == session_id
        assert session["title"] == title
        assert "started_at" in session
