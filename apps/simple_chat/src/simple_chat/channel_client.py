"""DesktopChannel client for Simple Chat.

This module provides a client to connect to CoPaw's DesktopChannel
and send/receive messages.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable, Optional

try:
    import websockets
except ImportError:
    websockets = None

logger = logging.getLogger(__name__)


class DesktopChannelClient:
    """Client for CoPaw DesktopChannel WebSocket connection.
    
    Provides simple send/receive interface for chat messages.
    
    Example:
        client = DesktopChannelClient("ws://localhost:8088/desktop/ws")
        await client.connect()
        await client.send_message("Hello!")
        await client.close()
    """
    
    def __init__(
        self,
        ws_url: str = "ws://127.0.0.1:8088/desktop/ws",
        on_message: Optional[Callable[[dict], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Initialize DesktopChannel client.
        
        Args:
            ws_url: WebSocket URL for DesktopChannel.
            on_message: Callback for received messages.
            on_error: Callback for errors.
        """
        if websockets is None:
            raise ImportError(
                "websockets library is required. "
                "Install with: pip install websockets"
            )
        
        self.ws_url = ws_url
        self.on_message = on_message
        self.on_error = on_error
        
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._is_connected = False
        self._receive_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """Connect to DesktopChannel WebSocket.
        
        Returns:
            True if connected successfully.
        """
        try:
            self._ws = await websockets.connect(self.ws_url)
            self._is_connected = True
            
            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            logger.info(f"Connected to DesktopChannel: {self.ws_url}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to connect to DesktopChannel: {e}")
            
            if self.on_error:
                self.on_error(e)
            
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from DesktopChannel."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._is_connected = False
        logger.info("Disconnected from DesktopChannel")
    
    async def send_message(self, text: str) -> bool:
        """Send text message to CoPaw.
        
        Args:
            text: Message text to send.
        
        Returns:
            True if sent successfully.
        """
        if not self._is_connected or not self._ws:
            logger.warning("Not connected to DesktopChannel")
            return False
        
        try:
            message = {
                "type": "text",
                "content": text,
            }
            
            await self._ws.send(json.dumps(message))
            
            logger.debug(f"Sent message: {text[:50]}...")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            
            if self.on_error:
                self.on_error(e)
            
            return False
    
    async def _receive_loop(self) -> None:
        """Receive messages from WebSocket."""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    
                    if self.on_message:
                        self.on_message(data)
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        
        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
        
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
            
            if self.on_error:
                self.on_error(e)
    
    def is_connected(self) -> bool:
        """Check if connected to DesktopChannel.
        
        Returns:
            True if connected.
        """
        return self._is_connected
