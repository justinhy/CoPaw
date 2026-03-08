"""Network communication module for WebSocket-based connections.

This module provides a robust WebSocket client with automatic reconnection,
message queuing, and state management for the CoPaw Desktop application.
"""
from __future__ import annotations

import asyncio
import json
import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    from websockets.exceptions import ConnectionClosed, ConnectionClosedError
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = None

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


@dataclass
class WebSocketConfig:
    """Configuration for WebSocket client.
    
    Attributes:
        url: WebSocket server URL (e.g., ws://127.0.0.1:8088/desktop/ws)
        max_reconnect_attempts: Maximum number of reconnection attempts (0 = infinite)
        reconnect_delay_base: Base delay in seconds for exponential backoff
        reconnect_delay_max: Maximum delay in seconds between reconnection attempts
        ping_interval: Interval in seconds for WebSocket keepalive pings
        ping_timeout: Timeout in seconds for ping response
        message_queue_size: Maximum size of outgoing message queue
    """
    url: str
    max_reconnect_attempts: int = 0  # 0 = infinite
    reconnect_delay_base: float = 1.0
    reconnect_delay_max: float = 30.0
    ping_interval: float = 20.0
    ping_timeout: float = 10.0
    message_queue_size: int = 100


class WebSocketClient:
    """Robust WebSocket client with auto-reconnect and message queuing.
    
    Features:
    - Automatic reconnection with exponential backoff
    - Outgoing message queue for reliable delivery
    - Connection state tracking and callbacks
    - Async context manager support
    
    Example:
        async with WebSocketClient("ws://localhost:8088/ws") as client:
            await client.send({"type": "text", "content": "Hello"})
            # Messages received via callbacks
    """
    
    def __init__(
        self,
        url: str,
        config: Optional[WebSocketConfig] = None,
    ) -> None:
        """Initialize WebSocketClient.
        
        Args:
            url: WebSocket server URL.
            config: Optional configuration object.
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets library not installed. "
                "Install with: pip install websockets"
            )
        
        self._config = config or WebSocketConfig(url=url)
        if url:
            self._config.url = url
        
        # Connection state
        self._state = ConnectionState.DISCONNECTED
        self._websocket: Optional[WebSocketClientProtocol] = None
        self._reconnect_attempts = 0
        self._should_reconnect = True
        
        # Message queues
        self._outgoing_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(
            maxsize=self._config.message_queue_size
        )
        
        # Callbacks
        self._message_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._state_callbacks: List[Callable[[ConnectionState], None]] = []
        self._error_callbacks: List[Callable[[Exception], None]] = []
        
        # Background tasks
        self._sender_task: Optional[asyncio.Task] = None
        self._receiver_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        
        # Session ID (optional, for server-side routing)
        self._session_id: Optional[str] = None
    
    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._state == ConnectionState.CONNECTED and self._websocket is not None
    
    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._session_id
    
    @session_id.setter
    def session_id(self, value: str) -> None:
        """Set session ID."""
        self._session_id = value
    
    def _set_state(self, new_state: ConnectionState) -> None:
        """Update connection state and notify callbacks.
        
        Args:
            new_state: New connection state.
        """
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            logger.debug(
                "WebSocket state changed: %s -> %s",
                old_state.value,
                new_state.value,
            )
            for callback in self._state_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    logger.exception("Error in state callback: %s", e)
    
    def on_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register callback for incoming messages.
        
        Args:
            callback: Function to call when message is received.
        """
        self._message_callbacks.append(callback)
    
    def on_state_change(self, callback: Callable[[ConnectionState], None]) -> None:
        """Register callback for connection state changes.
        
        Args:
            callback: Function to call when state changes.
        """
        self._state_callbacks.append(callback)
    
    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Register callback for errors.
        
        Args:
            callback: Function to call when error occurs.
        """
        self._error_callbacks.append(callback)
    
    def _notify_message(self, message: Dict[str, Any]) -> None:
        """Notify all message callbacks.
        
        Args:
            message: Received message dictionary.
        """
        for callback in self._message_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.exception("Error in message callback: %s", e)
    
    def _notify_error(self, error: Exception) -> None:
        """Notify all error callbacks.
        
        Args:
            error: Exception that occurred.
        """
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.exception("Error in error callback: %s", e)
    
    async def connect(self) -> bool:
        """Connect to WebSocket server.
        
        Returns:
            True if connected successfully.
        """
        if self.is_connected:
            logger.warning("Already connected")
            return True
        
        self._set_state(ConnectionState.CONNECTING)
        
        try:
            # Build URL with session_id if available
            url = self._config.url
            if self._session_id:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}session_id={self._session_id}"
            
            # Connect with ping/pong keepalive
            self._websocket = await websockets.connect(
                url,
                ping_interval=self._config.ping_interval,
                ping_timeout=self._config.ping_timeout,
            )
            
            self._reconnect_attempts = 0
            self._set_state(ConnectionState.CONNECTED)
            self._should_reconnect = True
            
            # Start background tasks
            self._sender_task = asyncio.create_task(self._send_loop())
            self._receiver_task = asyncio.create_task(self._receive_loop())
            
            logger.info("WebSocket connected to %s", self._config.url)
            return True
            
        except Exception as e:
            logger.error("Failed to connect: %s", e)
            self._set_state(ConnectionState.DISCONNECTED)
            self._notify_error(e)
            
            # Trigger reconnection if enabled
            if self._should_reconnect:
                asyncio.create_task(self._reconnect_loop())
            
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket server.
        
        This will stop automatic reconnection attempts.
        """
        self._should_reconnect = False
        
        # Cancel background tasks
        if self._sender_task:
            self._sender_task.cancel()
            try:
                await self._sender_task
            except asyncio.CancelledError:
                pass
            self._sender_task = None
        
        if self._receiver_task:
            self._receiver_task.cancel()
            try:
                await self._receiver_task
            except asyncio.CancelledError:
                pass
            self._receiver_task = None
        
        # Close WebSocket connection
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception as e:
                logger.debug("Error closing WebSocket: %s", e)
            self._websocket = None
        
        self._set_state(ConnectionState.DISCONNECTED)
        logger.info("WebSocket disconnected")
    
    async def send(self, message: Union[Dict[str, Any], str]) -> None:
        """Queue message for sending.
        
        Messages are queued and sent in the background send loop.
        If the queue is full, the oldest message is dropped.
        
        Args:
            message: Message dictionary or JSON string to send.
        """
        if isinstance(message, str):
            message = json.loads(message)
        
        try:
            # Use put_nowait to avoid blocking
            self._outgoing_queue.put_nowait(message)
        except asyncio.QueueFull:
            # Drop oldest message if queue is full
            try:
                self._outgoing_queue.get_nowait()
                self._outgoing_queue.put_nowait(message)
                logger.warning("Outgoing queue full, dropped oldest message")
            except asyncio.QueueEmpty:
                pass
    
    async def send_immediate(self, message: Union[Dict[str, Any], str]) -> bool:
        """Send message immediately without queuing.
        
        Args:
            message: Message dictionary or JSON string to send.
            
        Returns:
            True if sent successfully.
        """
        if not self.is_connected or not self._websocket:
            logger.warning("Cannot send: not connected")
            return False
        
        try:
            if isinstance(message, dict):
                data = json.dumps(message)
            else:
                data = message
            
            await self._websocket.send(data)
            return True
        except Exception as e:
            logger.error("Failed to send message: %s", e)
            self._notify_error(e)
            return False
    
    async def _send_loop(self) -> None:
        """Background task for sending queued messages."""
        while self.is_connected and self._websocket:
            try:
                # Wait for message from queue
                message = await asyncio.wait_for(
                    self._outgoing_queue.get(),
                    timeout=1.0
                )
                
                # Send message
                await self.send_immediate(message)
                
            except asyncio.TimeoutError:
                # No message in queue, continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in send loop: %s", e)
                break
    
    async def _receive_loop(self) -> None:
        """Background task for receiving messages."""
        while self.is_connected and self._websocket:
            try:
                # Receive message
                data = await self._websocket.recv()
                
                # Parse JSON
                try:
                    message = json.loads(data)
                    self._notify_message(message)
                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON received: %s", e)
                
            except ConnectionClosed:
                logger.info("WebSocket connection closed by server")
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in receive loop: %s", e)
                break
        
        # Connection lost, trigger reconnection
        if self._should_reconnect:
            self._set_state(ConnectionState.DISCONNECTED)
            asyncio.create_task(self._reconnect_loop())
    
    async def _reconnect_loop(self) -> None:
        """Background task for automatic reconnection."""
        self._set_state(ConnectionState.RECONNECTING)
        
        while self._should_reconnect:
            self._reconnect_attempts += 1
            
            # Check max attempts
            if (
                self._config.max_reconnect_attempts > 0
                and self._reconnect_attempts > self._config.max_reconnect_attempts
            ):
                logger.error(
                    "Max reconnection attempts (%d) reached",
                    self._config.max_reconnect_attempts,
                )
                self._set_state(ConnectionState.DISCONNECTED)
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                self._config.reconnect_delay_base * (2 ** (self._reconnect_attempts - 1)),
                self._config.reconnect_delay_max,
            )
            
            logger.info(
                "Reconnecting in %.1f seconds (attempt %d)",
                delay,
                self._reconnect_attempts,
            )
            
            await asyncio.sleep(delay)
            
            # Attempt reconnection
            if await self.connect():
                logger.info("Reconnection successful")
                break
    
    async def __aenter__(self) -> "WebSocketClient":
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
