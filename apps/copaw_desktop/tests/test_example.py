"""Example test to demonstrate TDD approach for CoPaw Desktop.

This test file will be replaced/expanded when implementing actual features.
"""

import pytest
from copaw_desktop.core.app_state import AppState


class TestAppState:
    """Tests for AppState enum - demonstrates TDD approach."""

    def test_app_state_has_idle(self) -> None:
        """Test that AppState has IDLE state."""
        assert hasattr(AppState, "IDLE")
        assert AppState.IDLE.value == "idle"

    def test_app_state_has_listening(self) -> None:
        """Test that AppState has LISTENING state."""
        assert hasattr(AppState, "LISTENING")
        assert AppState.LISTENING.value == "listening"

    def test_app_state_has_processing(self) -> None:
        """Test that AppState has PROCESSING state."""
        assert hasattr(AppState, "PROCESSING")
        assert AppState.PROCESSING.value == "processing"

    def test_app_state_has_speaking(self) -> None:
        """Test that AppState has SPEAKING state."""
        assert hasattr(AppState, "SPEAKING")
        assert AppState.SPEAKING.value == "speaking"

    def test_app_state_count(self) -> None:
        """Test that AppState has exactly 4 states."""
        assert len(list(AppState)) == 4


# Placeholder tests for future features
class TestSessionDBPlaceholder:
    """Placeholder tests for SessionDB - will be implemented in feat-003."""

    @pytest.mark.skip(reason="Waiting for feat-003 implementation")
    def test_create_session(self, temp_db_path: str) -> None:
        """Test session creation."""
        pass

    @pytest.mark.skip(reason="Waiting for feat-003 implementation")
    def test_get_sessions_grouped_by_hour(self, temp_db_path: str) -> None:
        """Test hourly grouping query."""
        pass


class TestWebSocketClientPlaceholder:
    """Placeholder tests for WebSocketClient - will be implemented in feat-002."""

    @pytest.mark.skip(reason="Waiting for feat-002 implementation")
    async def test_connect(self) -> None:
        """Test WebSocket connection."""
        pass

    @pytest.mark.skip(reason="Waiting for feat-002 implementation")
    async def test_send_receive(self) -> None:
        """Test sending and receiving messages."""
        pass
