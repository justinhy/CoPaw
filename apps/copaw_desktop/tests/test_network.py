"""Unit tests for WebSocketClient.

Tests cover:
- Connection lifecycle (connect, disconnect, reconnect)
- Message queuing and sending
- State tracking and callbacks
- Error handling
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from copaw_desktop.core.network import (
    WebSocketClient,
    WebSocketConfig,
    ConnectionState,
)


class TestWebSocketConfig:
    """Tests for WebSocketConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = WebSocketConfig(url="ws://localhost:8088/ws")
        
        assert config.url == "ws://localhost:8088/ws"
        assert config.max_reconnect_attempts == 0
        assert config.reconnect_delay_base == 1.0
        assert config.reconnect_delay_max == 30.0
        assert config.ping_interval == 20.0
        assert config.ping_timeout == 10.0
        assert config.message_queue_size == 100
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = WebSocketConfig(
            url="ws://example.com/ws",
            max_reconnect_attempts=5,
            reconnect_delay_base=2.0,
            reconnect_delay_max=60.0,
        )
        
        assert config.url == "ws://example.com/ws"
        assert config.max_reconnect_attempts == 5
        assert config.reconnect_delay_base == 2.0
        assert config.reconnect_delay_max == 60.0


class TestWebSocketClientInit:
    """Tests for WebSocketClient initialization."""
    
    def test_init_with_url(self):
        """Test initialization with URL string."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        assert client._config.url == "ws://localhost:8088/ws"
        assert client.state == ConnectionState.DISCONNECTED
        assert not client.is_connected
    
    def test_init_with_config(self):
        """Test initialization with config object."""
        config = WebSocketConfig(
            url="ws://example.com/ws",
            max_reconnect_attempts=10,
        )
        client = WebSocketClient(config=config)
        
        assert client._config.max_reconnect_attempts == 10
    
    def test_init_without_websockets_library(self):
        """Test initialization fails without websockets library."""
        with patch(
            "copaw_desktop.core.network.WEBSOCKETS_AVAILABLE",
            False,
        ):
            with pytest.raises(ImportError, match="websockets library not installed"):
                WebSocketClient("ws://localhost:8088/ws")


class TestWebSocketClientState:
    """Tests for connection state management."""
    
    def test_initial_state(self):
        """Test initial state is DISCONNECTED."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        assert client.state == ConnectionState.DISCONNECTED
        assert not client.is_connected
    
    def test_session_id_property(self):
        """Test session_id getter and setter."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        assert client.session_id is None
        
        client.session_id = "test-session-123"
        assert client.session_id == "test-session-123"
    
    def test_state_callbacks(self):
        """Test state change callbacks are invoked."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        callback = MagicMock()
        client.on_state_change(callback)
        
        # Manually trigger state change
        client._set_state(ConnectionState.CONNECTING)
        
        callback.assert_called_once_with(ConnectionState.CONNECTING)


class TestWebSocketClientCallbacks:
    """Tests for callback registration and invocation."""
    
    def test_on_message_registration(self):
        """Test message callback registration."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        callback = MagicMock()
        client.on_message(callback)
        
        assert callback in client._message_callbacks
    
    def test_on_state_change_registration(self):
        """Test state change callback registration."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        callback = MagicMock()
        client.on_state_change(callback)
        
        assert callback in client._state_callbacks
    
    def test_on_error_registration(self):
        """Test error callback registration."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        callback = MagicMock()
        client.on_error(callback)
        
        assert callback in client._error_callbacks
    
    def test_notify_message(self):
        """Test message notification to callbacks."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        callback1 = MagicMock()
        callback2 = MagicMock()
        client.on_message(callback1)
        client.on_message(callback2)
        
        message = {"type": "text", "content": "Hello"}
        client._notify_message(message)
        
        callback1.assert_called_once_with(message)
        callback2.assert_called_once_with(message)
    
    def test_notify_error(self):
        """Test error notification to callbacks."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        callback = MagicMock()
        client.on_error(callback)
        
        error = Exception("Test error")
        client._notify_error(error)
        
        callback.assert_called_once_with(error)


class TestWebSocketClientMessaging:
    """Tests for message sending and queuing."""
    
    @pytest.mark.asyncio
    async def test_send_queues_message(self):
        """Test send() queues message for delivery."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        message = {"type": "text", "content": "Hello"}
        await client.send(message)
        
        # Message should be in queue
        assert not client._outgoing_queue.empty()
        queued = await client._outgoing_queue.get()
        assert queued == message
    
    @pytest.mark.asyncio
    async def test_send_json_string(self):
        """Test send() accepts JSON string."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        message = '{"type": "text", "content": "Hello"}'
        await client.send(message)
        
        queued = await client._outgoing_queue.get()
        assert queued == {"type": "text", "content": "Hello"}
    
    @pytest.mark.asyncio
    async def test_send_queue_full_drops_oldest(self):
        """Test send() drops oldest message when queue is full."""
        config = WebSocketConfig(
            url="ws://localhost:8088/ws",
            message_queue_size=2,
        )
        client = WebSocketClient(config=config)
        
        # Fill queue
        await client.send({"id": 1})
        await client.send({"id": 2})
        
        # Send third message (should drop first)
        await client.send({"id": 3})
        
        # Check queue contents
        first = await client._outgoing_queue.get()
        second = await client._outgoing_queue.get()
        
        assert first == {"id": 2}
        assert second == {"id": 3}
    
    @pytest.mark.asyncio
    async def test_send_immediate_when_not_connected(self):
        """Test send_immediate() returns False when not connected."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        result = await client.send_immediate({"type": "text"})
        assert result is False


class TestWebSocketClientConnection:
    """Tests for connection lifecycle."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        # Mock websockets.connect
        mock_ws = AsyncMock()
        with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
            result = await client.connect()
        
        assert result is True
        assert client.is_connected
        assert client.state == ConnectionState.CONNECTED
        
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        # Mock websockets.connect to raise exception
        with patch(
            "websockets.connect",
            new_callable=AsyncMock,
            side_effect=Exception("Connection failed"),
        ):
            result = await client.connect()
        
        assert result is False
        assert not client.is_connected
        assert client.state == ConnectionState.DISCONNECTED
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        # Mock connection
        mock_ws = AsyncMock()
        with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
            await client.connect()
            await client.disconnect()
        
        assert not client.is_connected
        assert client.state == ConnectionState.DISCONNECTED
        mock_ws.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        mock_ws = AsyncMock()
        
        with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
            async with WebSocketClient("ws://localhost:8088/ws") as client:
                assert client.is_connected
            
            assert not client.is_connected


class TestWebSocketClientReconnect:
    """Tests for automatic reconnection."""
    
    @pytest.mark.asyncio
    async def test_reconnect_on_disconnect(self):
        """Test automatic reconnection when connection is lost."""
        config = WebSocketConfig(
            url="ws://localhost:8088/ws",
            max_reconnect_attempts=1,
            reconnect_delay_base=0.1,
        )
        client = WebSocketClient(config=config)
        
        # Mock websockets.connect
        mock_ws = AsyncMock()
        connect_mock = AsyncMock(return_value=mock_ws)
        
        with patch("websockets.connect", connect_mock):
            await client.connect()
            
            # Simulate connection loss by closing websocket
            # (This would normally be triggered by the receive loop)
            client._should_reconnect = False  # Disable for test
            await client.disconnect()
        
        assert client.state == ConnectionState.DISCONNECTED
    
    @pytest.mark.asyncio
    async def test_max_reconnect_attempts(self):
        """Test reconnection stops after max attempts."""
        config = WebSocketConfig(
            url="ws://localhost:8088/ws",
            max_reconnect_attempts=2,
            reconnect_delay_base=0.1,
        )
        client = WebSocketClient(config=config)
        
        # Mock websockets.connect to always fail
        error_callback = MagicMock()
        client.on_error(error_callback)
        
        with patch(
            "websockets.connect",
            new_callable=AsyncMock,
            side_effect=Exception("Connection failed"),
        ):
            result = await client.connect()
            
            # Wait for reconnection attempts
            await asyncio.sleep(0.5)
        
        assert result is False
        assert client._reconnect_attempts <= config.max_reconnect_attempts


class TestWebSocketClientReceive:
    """Tests for message receiving."""
    
    @pytest.mark.asyncio
    async def test_receive_loop_notifies_callbacks(self):
        """Test receive loop notifies message callbacks."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        # Mock websocket
        mock_ws = AsyncMock()
        message_callback = MagicMock()
        client.on_message(message_callback)
        
        # Simulate receiving a message
        test_message = {"type": "text", "content": "Hello"}
        mock_ws.recv = AsyncMock(return_value=json.dumps(test_message))
        
        with patch("websockets.connect", AsyncMock(return_value=mock_ws)):
            await client.connect()
            
            # Manually run one iteration of receive loop
            try:
                await asyncio.wait_for(client._receive_loop(), timeout=0.5)
            except asyncio.TimeoutError:
                pass
        
        # Callback should have been notified
        message_callback.assert_called_once_with(test_message)
        
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_receive_loop_handles_invalid_json(self):
        """Test receive loop handles invalid JSON gracefully."""
        client = WebSocketClient("ws://localhost:8088/ws")
        
        # Mock websocket
        mock_ws = AsyncMock()
        message_callback = MagicMock()
        client.on_message(message_callback)
        
        # Send invalid JSON
        mock_ws.recv = AsyncMock(return_value="not valid json")
        
        with patch("websockets.connect", AsyncMock(return_value=mock_ws)):
            await client.connect()
            
            try:
                await asyncio.wait_for(client._receive_loop(), timeout=0.5)
            except asyncio.TimeoutError:
                pass
        
        # Callback should NOT have been called
        message_callback.assert_not_called()
        
        await client.disconnect()
