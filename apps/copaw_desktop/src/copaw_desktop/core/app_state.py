"""Application state management."""

from enum import Enum


class AppState(Enum):
    """Application state machine states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
