# -*- coding: utf-8 -*-
"""Integration tests for DesktopChannel."""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from copaw.app.channels.desktop import DesktopChannel
from copaw.app.channels.desktop.channel import DesktopConnectionManager


class TestDesktopConnectionManager:
    """Tests for DesktopConnectionManager."""

    def test_init(self):
        """Test manager initialization."""
        manager = DesktopConnectionManager()
        assert len(manager._connections) == 0
        assert len(manager._active_session_ids) == 0

    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connect and disconnect flow."""
        manager = DesktopConnectionManager()
        websocket = AsyncMock()
        session_id = "test-session-123"

        # Connect
        await manager.connect(session_id, websocket)
        assert session_id in manager._connections
        assert session_id in manager._active_session_ids
        websocket.accept.assert_called_once()

        # Disconnect
        manager.disconnect(session_id)
        assert session_id not in manager._connections
        assert session_id not in manager._active_session_ids

    @pytest.mark.asyncio
    async def test_send_text(self):
        """Test sending text to a session."""
        manager = DesktopConnectionManager()
        websocket = AsyncMock()
        session_id = "test-session-456"

        await manager.connect(session_id, websocket)
        await manager.send_text(session_id, "Hello, World!", is_final=False)

        # Verify message was sent
        websocket.send_json.assert_called_once()
        call_args = websocket.send_json.call_args[0][0]
        assert call_args["type"] == "text_chunk"
        assert call_args["content"] == "Hello, World!"
        assert call_args["is_final"] is False

    @pytest.mark.asyncio
    async def test_send_widget(self):
        """Test sending widget data to a session."""
        manager = DesktopConnectionManager()
        websocket = AsyncMock()
        session_id = "test-session-789"

        await manager.connect(session_id, websocket)
        widget_data = {"url": "https://example.com/image.png"}
        await manager.send_widget(session_id, "image", widget_data)

        # Verify message was sent
        websocket.send_json.assert_called_once()
        call_args = websocket.send_json.call_args[0][0]
        assert call_args["type"] == "widget"
        assert call_args["widget_type"] == "image"
        assert call_args["data"] == widget_data

    @pytest.mark.asyncio
    async def test_send_to_disconnected_session(self):
        """Test sending to a disconnected session (should not raise)."""
        manager = DesktopConnectionManager()
        # Try to send to non-existent session
        await manager.send_text("non-existent-session", "Hello", is_final=True)
        # Should complete without error


class TestDesktopChannel:
    """Tests for DesktopChannel."""

    def test_channel_type(self):
        """Test channel type identifier."""
        assert DesktopChannel.channel == "desktop"

    def test_uses_manager_queue_false(self):
        """Test that desktop channel does not use manager queue."""
        assert DesktopChannel.uses_manager_queue is False

    def test_from_env(self):
        """Test creating channel from environment."""
        process = MagicMock()
        channel = DesktopChannel.from_env(process)
        assert channel.enabled is True
        assert channel.process == process

    def test_from_env_disabled(self):
        """Test creating disabled channel from environment."""
        process = MagicMock()
        with patch.dict("os.environ", {"DESKTOP_CHANNEL_ENABLED": "0"}):
            channel = DesktopChannel.from_env(process)
            assert channel.enabled is False

    def test_from_config(self):
        """Test creating channel from config."""
        process = MagicMock()
        config = MagicMock()
        config.enabled = True
        
        channel = DesktopChannel.from_config(process, config)
        assert channel.enabled is True
        assert channel.process == process

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test channel start and stop."""
        process = MagicMock()
        channel = DesktopChannel(process, enabled=True)
        
        # Start
        await channel.start()
        assert channel._running is True
        
        # Stop
        await channel.stop()
        assert channel._running is False

    @pytest.mark.asyncio
    async def test_start_disabled(self):
        """Test starting disabled channel."""
        process = MagicMock()
        channel = DesktopChannel(process, enabled=False)
        
        await channel.start()
        assert channel._running is False

    def test_build_agent_request_from_native(self):
        """Test building AgentRequest from native payload."""
        process = MagicMock()
        channel = DesktopChannel(process)
        
        payload = {
            "type": "text",
            "content": "Hello, CoPaw!",
            "session_id": "session-123",
            "user_id": "user-456",
        }
        
        request = channel.build_agent_request_from_native(payload)
        
        assert request.session_id == "session-123"
        assert request.user_id == "user-456"
        assert request.channel == "desktop"
        assert len(request.input) == 1
        assert request.input[0].content[0].text == "Hello, CoPaw!"

    def test_build_agent_request_from_json_string(self):
        """Test building AgentRequest from JSON string."""
        process = MagicMock()
        channel = DesktopChannel(process)
        
        payload = json.dumps({
            "type": "text",
            "content": "Test message",
        })
        
        request = channel.build_agent_request_from_native(payload)
        assert request.session_id  # Should generate UUID
        assert request.input[0].content[0].text == "Test message"

    @pytest.mark.asyncio
    async def test_send(self):
        """Test sending text to a session."""
        process = MagicMock()
        channel = DesktopChannel(process)
        
        # Mock connection manager
        channel.connection_manager.send_text = AsyncMock()
        
        await channel.send("session-123", "Hello!")
        
        channel.connection_manager.send_text.assert_called_once_with(
            session_id="session-123",
            text="Hello!",
            is_final=True,
        )


class TestDesktopChannelIntegration:
    """Integration tests for DesktopChannel with WebSocket."""

    @pytest.mark.asyncio
    async def test_websocket_message_flow(self):
        """Test complete WebSocket message flow."""
        from fastapi import WebSocket
        
        process = AsyncMock()
        # Mock the process to return a simple event stream
        async def mock_process(request):
            from agentscope_runtime.engine.schemas.agent_schemas import Event
            yield Event(status="completed")
        
        process.side_effect = mock_process
        
        channel = DesktopChannel(process)
        await channel.start()
        
        # Mock WebSocket
        websocket = AsyncMock(spec=WebSocket)
        websocket.query_params = {"session_id": "test-session"}
        websocket.receive_text = AsyncMock(return_value=json.dumps({
            "type": "text",
            "content": "Hello",
        }))
        
        # Make receive_text raise WebSocketDisconnect after one message
        from fastapi import WebSocketDisconnect
        websocket.receive_text.side_effect = [
            json.dumps({"type": "text", "content": "Hello"}),
            WebSocketDisconnect(),
        ]
        
        # Handle WebSocket (will run until disconnect)
        await channel.handle_websocket(websocket)
        
        # Verify connection was cleaned up
        assert "test-session" not in channel.connection_manager._active_session_ids
        
        await channel.stop()
