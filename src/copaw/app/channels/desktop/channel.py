# -*- coding: utf-8 -*-
"""Desktop Channel: WebSocket-based channel for CoPaw Desktop application.

This channel provides a WebSocket endpoint for desktop clients to interact
with CoPaw through real-time bidirectional communication.

Protocol:
- Client -> Server: {"type": "text", "content": "...", "session_id": "..."}
- Server -> Client: {"type": "text_chunk", "content": "...", "is_final": bool}
- Server -> Client: {"type": "widget", "widget_type": "...", "data": {...}}
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from ..base import BaseChannel, OnReplySent, ProcessHandler

logger = logging.getLogger(__name__)


class DesktopConnectionManager:
    """Manages active WebSocket connections for DesktopChannel.
    
    Provides connection lifecycle management and message broadcasting.
    """

    def __init__(self) -> None:
        """Initialize connection manager."""
        # Map session_id -> WebSocket
        self._connections: Dict[str, WebSocket] = {}
        # Track all active connection IDs for cleanup
        self._active_session_ids: Set[str] = set()

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            session_id: Unique session identifier.
            websocket: WebSocket connection instance.
        """
        await websocket.accept()
        self._connections[session_id] = websocket
        self._active_session_ids.add(session_id)
        logger.info("Desktop client connected: session_id=%s", session_id)

    def disconnect(self, session_id: str) -> None:
        """Remove a WebSocket connection from the manager.

        Args:
            session_id: Session identifier to disconnect.
        """
        if session_id in self._connections:
            del self._connections[session_id]
        self._active_session_ids.discard(session_id)
        logger.info("Desktop client disconnected: session_id=%s", session_id)

    async def send_text(
        self,
        session_id: str,
        text: str,
        is_final: bool = False,
    ) -> None:
        """Send text chunk to a specific session.

        Args:
            session_id: Target session identifier.
            text: Text content to send.
            is_final: Whether this is the final chunk.
        """
        websocket = self._connections.get(session_id)
        if websocket:
            try:
                message = {
                    "type": "text_chunk",
                    "content": text,
                    "is_final": is_final,
                }
                await websocket.send_json(message)
            except Exception as e:
                logger.exception(
                    "Failed to send text to session %s: %s",
                    session_id,
                    e,
                )
                self.disconnect(session_id)

    async def send_widget(
        self,
        session_id: str,
        widget_type: str,
        data: Dict[str, Any],
    ) -> None:
        """Send widget data to a specific session.

        Args:
            session_id: Target session identifier.
            widget_type: Type of widget (image, chart, markdown).
            data: Widget data payload.
        """
        websocket = self._connections.get(session_id)
        if websocket:
            try:
                message = {
                    "type": "widget",
                    "widget_type": widget_type,
                    "data": data,
                }
                await websocket.send_json(message)
            except Exception as e:
                logger.exception(
                    "Failed to send widget to session %s: %s",
                    session_id,
                    e,
                )
                self.disconnect(session_id)

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs.

        Returns:
            List of active session identifiers.
        """
        return list(self._active_session_ids)


class DesktopChannel(BaseChannel):
    """CoPaw Desktop channel for WebSocket-based desktop clients.

    This channel exposes a WebSocket endpoint at `/desktop/ws` that desktop
    applications can connect to for real-time interaction with CoPaw.

    Unlike other channels, DesktopChannel manages its own WebSocket connections
    directly (uses_manager_queue = False) because each connection represents
    a long-lived session.
    """

    channel = "desktop"
    uses_manager_queue = False

    def __init__(
        self,
        process: ProcessHandler,
        enabled: bool = True,
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
    ) -> None:
        """Initialize DesktopChannel.

        Args:
            process: Handler for agent requests.
            enabled: Whether this channel is active.
            on_reply_sent: Callback when reply is sent.
            show_tool_details: Whether to show tool execution details.
            filter_tool_messages: Whether to filter out tool messages.
            filter_thinking: Whether to filter thinking/reasoning blocks.
        """
        super().__init__(
            process,
            on_reply_sent,
            show_tool_details,
            filter_tool_messages=filter_tool_messages,
            filter_thinking=filter_thinking,
        )
        self.enabled = enabled
        self.connection_manager = DesktopConnectionManager()
        self._running = False

    @classmethod
    def from_env(
        cls,
        process: ProcessHandler,
        on_reply_sent: OnReplySent = None,
    ) -> "DesktopChannel":
        """Create DesktopChannel from environment variables.

        Args:
            process: Handler for agent requests.
            on_reply_sent: Callback when reply is sent.

        Returns:
            Configured DesktopChannel instance.
        """
        import os

        return cls(
            process=process,
            enabled=os.getenv("DESKTOP_CHANNEL_ENABLED", "1") == "1",
            on_reply_sent=on_reply_sent,
        )

    @classmethod
    def from_config(
        cls,
        process: ProcessHandler,
        config: Any,
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
    ) -> "DesktopChannel":
        """Create DesktopChannel from config object.

        Args:
            process: Handler for agent requests.
            config: Desktop channel configuration.
            on_reply_sent: Callback when reply is sent.
            show_tool_details: Whether to show tool execution details.
            filter_tool_messages: Whether to filter out tool messages.
            filter_thinking: Whether to filter thinking/reasoning blocks.

        Returns:
            Configured DesktopChannel instance.
        """
        return cls(
            process=process,
            enabled=getattr(config, "enabled", True),
            on_reply_sent=on_reply_sent,
            show_tool_details=show_tool_details,
            filter_tool_messages=filter_tool_messages,
            filter_thinking=filter_thinking,
        )

    async def start(self) -> None:
        """Start the desktop channel.

        The actual WebSocket endpoint is registered in the router layer.
        This method initializes internal state.
        """
        if not self.enabled:
            logger.info("Desktop channel disabled, skipping start")
            return

        self._running = True
        logger.info("Desktop channel started")

    async def stop(self) -> None:
        """Stop the desktop channel and close all connections."""
        self._running = False

        # Close all active connections
        for session_id in self.connection_manager.get_active_sessions():
            try:
                websocket = self.connection_manager._connections.get(session_id)
                if websocket:
                    await websocket.close(code=1000, reason="Server shutting down")
            except Exception:
                logger.exception(
                    "Error closing WebSocket for session %s",
                    session_id,
                )
            finally:
                self.connection_manager.disconnect(session_id)

        logger.info("Desktop channel stopped")

    async def send(
        self,
        to_handle: str,
        text: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send text to a desktop client session.

        Args:
            to_handle: Session ID to send to.
            text: Text content to send.
            meta: Optional metadata (e.g., widget data).
        """
        await self.connection_manager.send_text(
            session_id=to_handle,
            text=text,
            is_final=True,
        )

    def build_agent_request_from_native(self, native_payload: Any) -> Any:
        """Convert a desktop message payload to AgentRequest.

        Args:
            native_payload: Raw message from desktop client.

        Returns:
            AgentRequest instance.
        """
        from agentscope_runtime.engine.schemas.agent_schemas import (
            AgentRequest,
            Message,
            MessageType,
            Role,
            TextContent,
            ContentType,
        )

        # Parse payload
        if isinstance(native_payload, str):
            payload = json.loads(native_payload)
        else:
            payload = native_payload if isinstance(native_payload, dict) else {}

        # Extract fields
        content = payload.get("content", "")
        session_id = payload.get("session_id", str(uuid.uuid4()))
        user_id = payload.get("user_id", "desktop_user")

        # Build AgentRequest
        msg = Message(
            type=MessageType.MESSAGE,
            role=Role.USER,
            content=[TextContent(type=ContentType.TEXT, text=content)],
        )

        return AgentRequest(
            session_id=session_id,
            user_id=user_id,
            input=[msg],
            channel=self.channel,
        )

    async def handle_websocket(self, websocket: WebSocket) -> None:
        """Handle a WebSocket connection from a desktop client.

        This method is called by the router when a new WebSocket connection
        is established.

        Args:
            websocket: WebSocket connection instance.
        """
        # Generate or extract session ID
        session_id = websocket.query_params.get("session_id", str(uuid.uuid4()))

        # Register connection
        await self.connection_manager.connect(session_id, websocket)

        try:
            # Message processing loop
            while self._running:
                # Receive message from client
                raw_data = await websocket.receive_text()

                try:
                    # Parse JSON message
                    payload = json.loads(raw_data)
                    message_type = payload.get("type", "text")

                    if message_type == "text":
                        # Build AgentRequest from native payload
                        payload["session_id"] = session_id
                        request = self.build_agent_request_from_native(payload)

                        # Process through agent and stream response
                        await self._process_and_stream(request, session_id)
                    else:
                        logger.warning(
                            "Unknown message type from desktop client: %s",
                            message_type,
                        )

                except json.JSONDecodeError as e:
                    logger.exception("Invalid JSON from desktop client: %s", e)
                    await self.connection_manager.send_text(
                        session_id,
                        f"Error: Invalid JSON format",
                        is_final=True,
                    )

        except WebSocketDisconnect:
            logger.info("Desktop client disconnected: session_id=%s", session_id)
        except Exception as e:
            logger.exception("Error in desktop WebSocket handler: %s", e)
        finally:
            self.connection_manager.disconnect(session_id)

    async def _process_and_stream(
        self,
        request: Any,
        session_id: str,
    ) -> None:
        """Process an AgentRequest and stream the response to the client.

        Args:
            request: AgentRequest to process.
            session_id: Session identifier for response routing.
        """
        try:
            # Process through agent (streaming)
            accumulated_text = ""

            async for event in self._process(request):
                # Handle different event types
                if hasattr(event, "content") and event.content:
                    for part in event.content:
                        if hasattr(part, "text") and part.text:
                            # Stream text chunks
                            accumulated_text += part.text
                            await self.connection_manager.send_text(
                                session_id,
                                part.text,
                                is_final=False,
                            )

                        elif hasattr(part, "type"):
                            # Handle widget content (images, charts, etc.)
                            part_type = part.type
                            widget_data = {}

                            if part_type == "image" and hasattr(part, "url"):
                                widget_data = {"url": part.url}
                                await self.connection_manager.send_widget(
                                    session_id,
                                    "image",
                                    widget_data,
                                )
                            elif part_type == "chart":
                                # Chart data is expected in part.data
                                widget_data = getattr(part, "data", {})
                                await self.connection_manager.send_widget(
                                    session_id,
                                    "chart",
                                    widget_data,
                                )

                # Check if this is the final event
                if hasattr(event, "status") and str(event.status) == "completed":
                    # Send final marker
                    if accumulated_text:
                        await self.connection_manager.send_text(
                            session_id,
                            "",
                            is_final=True,
                        )

        except Exception as e:
            logger.exception("Error processing request for session %s: %s", session_id, e)
            await self.connection_manager.send_text(
                session_id,
                f"Error: {str(e)}",
                is_final=True,
            )
