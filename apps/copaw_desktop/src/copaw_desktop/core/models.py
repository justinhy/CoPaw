"""Data models for session and message storage.

This module defines the SQLAlchemy ORM models for persisting
chat sessions and messages in a local SQLite database.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    String,
    DateTime,
    ForeignKey,
    Text,
    create_engine,
    Column,
    Integer,
    orm_declarative_base,
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SessionModel(Base):
    """SQLAlchemy model for chat sessions.
    
    Attributes:
        id: Unique session identifier (UUID string)
        title: Optional session title
        started_at: Session creation timestamp
        updated_at: Last update timestamp
        messages: Relationship to MessageModel
    """
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    # Relationship
    messages = relationship(
        "MessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class MessageModel(Base):
    """SQLAlchemy model for chat messages.
    
    Attributes:
        id: Unique message identifier (UUID string)
        session_id: Foreign key to session
        role: Message role ("user" or "assistant")
        content: Message text content
        created_at: Message creation timestamp
        widget_data: Optional JSON data for widgets (images, charts)
    """
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    widget_data = Column(JSON, nullable=True)
    
    # Relationship
    session = relationship("SessionModel", back_populates="messages")
