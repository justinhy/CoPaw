# -*- coding: utf-8 -*-
"""Desktop channel router.

Exports ``desktop_router`` with WebSocket endpoint mounted at the app root:
``/desktop/ws`` - WebSocket endpoint for desktop clients.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Desktop-facing router (mounted at root level)
# ---------------------------------------------------------------------------
desktop_router = APIRouter(tags=["desktop"])


def _get_desktop_channel(request_or_ws):
    """Retrieve the DesktopChannel from app state, or None.

    Args:
        request_or_ws: FastAPI Request or WebSocket object.

    Returns:
        DesktopChannel instance or None if not found.
    """
    app = getattr(request_or_ws, "app", None)
    if not app:
        return None
    cm = getattr(app.state, "channel_manager", None)
    if not cm:
        return None
    for ch in cm.channels:
        if ch.channel == "desktop":
            return ch
    return None


@desktop_router.websocket("/desktop/ws")
async def desktop_ws(websocket: WebSocket) -> None:
    """Desktop WebSocket endpoint.

    This endpoint accepts WebSocket connections from desktop clients.
    Each connection is identified by an optional session_id query parameter.
    If not provided, a new session_id will be generated.

    Protocol:
    - Client -> Server: {"type": "text", "content": "...", "session_id": "..."}
    - Server -> Client: {"type": "text_chunk", "content": "...", "is_final": bool}
    - Server -> Client: {"type": "widget", "widget_type": "...", "data": {...}}

    Query Parameters:
        session_id: Optional session identifier. If not provided, a new one
                   will be generated.
    """
    desktop_ch = _get_desktop_channel(websocket)
    if not desktop_ch:
        logger.warning("Desktop channel not available, rejecting connection")
        await websocket.close(code=1008, reason="Desktop channel not available")
        return

    if not desktop_ch.enabled:
        logger.warning("Desktop channel disabled, rejecting connection")
        await websocket.close(code=1008, reason="Desktop channel disabled")
        return

    # Delegate connection handling to the channel
    await desktop_ch.handle_websocket(websocket)
