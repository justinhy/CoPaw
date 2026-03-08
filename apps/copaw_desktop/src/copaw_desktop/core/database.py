"""Database module for session storage.

This module provides a SQLite-based storage backend for chat sessions
and messages using SQLAlchemy ORM.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, SessionModel, MessageModel


class SessionDB:
    """SQLite-based session storage using SQLAlchemy ORM.
    
    Provides CRUD operations for sessions and messages with automatic
    hourly grouping for UI display.
    
    Example:
        db = SessionDB("~/.copaw_desktop/sessions.db")
        session_id = db.create_session("My Chat")
        db.add_message(session_id, "user", "Hello!")
        messages = db.get_messages(session_id)
    """
    
    def __init__(self, db_path: str = ":memory:") -> None:
        """Initialize SessionDB.
        
        Args:
            db_path: Path to SQLite database file. Use ":memory:" for testing.
        """
        # Expand ~ to home directory
        if db_path != ":memory:":
            db_path = str(Path(db_path).expanduser())
            # Ensure parent directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create SQLAlchemy engine
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            future=True,
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False,
        )
    
    def create_session(self, title: Optional[str] = None) -> str:
        """Create a new session.
        
        Args:
            title: Optional session title.
        
        Returns:
            Session ID (UUID string).
        """
        session_id = str(uuid.uuid4())
        
        with self.SessionLocal() as session:
            try:
                session_model = SessionModel(
                    id=session_id,
                    title=title,
                    started_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(session_model)
                session.commit()
                return session_id
            except SQLAlchemyError as e:
                session.rollback()
                raise RuntimeError(f"Failed to create session: {e}") from e
    
    def get_sessions_grouped_by_hour(self) -> Dict[date, Dict[int, List[Dict]]]:
        """Get all sessions grouped by date and hour.
        
        Returns:
            Dictionary with structure:
            {
                date(2024-01-15): {
                    hour(14): [
                        {"id": "session-1", "title": "...", "started_at": "...", ...},
                        ...
                    ],
                    hour(15): [...]
                },
                ...
            }
        """
        with self.SessionLocal() as session:
            try:
                # Query all sessions ordered by started_at descending
                sessions = (
                    session.query(SessionModel)
                    .order_by(desc(SessionModel.started_at))
                    .all()
                )
                
                # Group by date and hour
                result: Dict[date, Dict[int, List[Dict]]] = defaultdict(
                    lambda: defaultdict(list)
                )
                
                for sess in sessions:
                    sess_date = sess.started_at.date()
                    sess_hour = sess.started_at.hour()
                    
                    session_dict = {
                        "id": sess.id,
                        "title": sess.title,
                        "started_at": sess.started_at.isoformat(),
                        "updated_at": sess.updated_at.isoformat(),
                    }
                    
                    result[sess_date][sess_hour].append(session_dict)
                
                # Convert defaultdicts to regular dicts for JSON serialization
                return {
                    date_key: {
                        hour_key: hour_list
                        for hour_key, hour_list in hour_dict.items()
                    }
                    for date_key, hour_dict in result.items()
                }
                
            except SQLAlchemyError as e:
                raise RuntimeError(f"Failed to get sessions: {e}") from e
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        widget_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add message to session.
        
        Args:
            session_id: Session ID.
            role: Message role ("user" or "assistant").
            content: Message content.
            widget_data: Optional widget data for images/charts.
        
        Returns:
            Message ID (UUID string).
        """
        message_id = str(uuid.uuid4())
        
        with self.SessionLocal() as session:
            try:
                # Verify session exists
                session_model = (
                    session.query(SessionModel)
                    .filter(SessionModel.id == session_id)
                    .first()
                )
                
                if not session_model:
                    raise ValueError(f"Session {session_id} not found")
                
                # Create message
                message_model = MessageModel(
                    id=message_id,
                    session_id=session_id,
                    role=role,
                    content=content,
                    created_at=datetime.utcnow(),
                    widget_data=widget_data,
                )
                
                session.add(message_model)
                
                # Update session's updated_at timestamp
                session_model.updated_at = datetime.utcnow()
                
                session.commit()
                return message_id
                
            except ValueError:
                raise
            except SQLAlchemyError as e:
                session.rollback()
                raise RuntimeError(f"Failed to add message: {e}") from e
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session.
        
        Args:
            session_id: Session ID.
        
        Returns:
            List of message dictionaries, ordered by created_at ascending.
        """
        with self.SessionLocal() as session:
            try:
                messages = (
                    session.query(MessageModel)
                    .filter(MessageModel.session_id == session_id)
                    .order_by(MessageModel.created_at)
                    .all()
                )
                
                return [
                    {
                        "id": msg.id,
                        "session_id": msg.session_id,
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                        "widget_data": msg.widget_data,
                    }
                    for msg in messages
                ]
                
            except SQLAlchemyError as e:
                raise RuntimeError(f"Failed to get messages: {e}") from e
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages.
        
        Args:
            session_id: Session ID.
        
        Returns:
            True if session was deleted, False if not found.
        """
        with self.SessionLocal() as session:
            try:
                # Delete session (messages will cascade delete)
                deleted = (
                    session.query(SessionModel)
                    .filter(SessionModel.id == session_id)
                    .delete()
                )
                
                session.commit()
                return deleted > 0
                
            except SQLAlchemyError as e:
                session.rollback()
                raise RuntimeError(f"Failed to delete session: {e}") from e
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title.
        
        Args:
            session_id: Session ID.
            title: New title.
        
        Returns:
            True if updated, False if not found.
        """
        with self.SessionLocal() as session:
            try:
                session_model = (
                    session.query(SessionModel)
                    .filter(SessionModel.id == session_id)
                    .first()
                )
                
                if not session_model:
                    return False
                
                session_model.title = title
                session_model.updated_at = datetime.utcnow()
                
                session.commit()
                return True
                
            except SQLAlchemyError as e:
                session.rollback()
                raise RuntimeError(f"Failed to update session title: {e}") from e
    
    def get_session_count(self) -> int:
        """Get total number of sessions.
        
        Returns:
            Number of sessions.
        """
        with self.SessionLocal() as session:
            try:
                return session.query(func.count(SessionModel.id)).scalar() or 0
            except SQLAlchemyError as e:
                raise RuntimeError(f"Failed to get session count: {e}") from e
    
    def get_message_count(self, session_id: Optional[str] = None) -> int:
        """Get total number of messages, optionally filtered by session.
        
        Args:
            session_id: Optional session ID to filter by.
        
        Returns:
            Number of messages.
        """
        with self.SessionLocal() as session:
            try:
                query = session.query(func.count(MessageModel.id))
                
                if session_id:
                    query = query.filter(MessageModel.session_id == session_id)
                
                return query.scalar() or 0
                
            except SQLAlchemyError as e:
                raise RuntimeError(f"Failed to get message count: {e}") from e
