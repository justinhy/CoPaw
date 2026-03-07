"""Pytest configuration and fixtures for CoPaw Desktop tests."""

import pytest
from pathlib import Path


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """Create a temporary database path for testing.

    Args:
        tmp_path: Pytest fixture providing temporary directory.

    Returns:
        Path to temporary database file.
    """
    return str(tmp_path / "test_sessions.db")


@pytest.fixture
def sample_audio_path() -> str:
    """Get path to sample audio file for testing.

    Returns:
        Path to sample audio file.
    """
    # Will be created when we add test audio files
    return "tests/fixtures/sample.wav"


@pytest.fixture
def sample_session_data() -> dict:
    """Get sample session data for testing.

    Returns:
        Dictionary with sample session data.
    """
    return {
        "id": "test-session-123",
        "title": "Test Session",
        "started_at": "2026-03-08T14:00:00Z",
    }


@pytest.fixture
def sample_message_data() -> dict:
    """Get sample message data for testing.

    Returns:
        Dictionary with sample message data.
    """
    return {
        "id": "test-message-456",
        "session_id": "test-session-123",
        "role": "user",
        "content": "Hello, CoPaw!",
        "created_at": "2026-03-08T14:01:00Z",
    }


@pytest.fixture
def sample_widget_data() -> dict:
    """Get sample widget data for testing.

    Returns:
        Dictionary with sample widget data.
    """
    return {
        "type": "chart",
        "data": {
            "xAxis": {"type": "category", "data": ["Mon", "Tue", "Wed"]},
            "yAxis": {"type": "value"},
            "series": [{"data": [120, 200, 150], "type": "bar"}],
        },
    }
