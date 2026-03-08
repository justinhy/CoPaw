"""
CoPaw Desktop - Cross-platform AI Voice Companion Application

This package provides a full-featured desktop client for CoPaw,
featuring voice interaction, chat interface, and dynamic content rendering.
"""

__version__ = "0.1.0"
__author__ = "AgentScope Team"
__email__ = "agentscope@alibaba-inc.com"

from copaw_desktop.core.app_state import AppState
from copaw_desktop.core.audio import AudioRecorder
from copaw_desktop.core.network import (
    WebSocketClient,
    WebSocketConfig,
    ConnectionState,
)
from copaw_desktop.core.database import SessionDB

__all__ = [
    "AppState",
    "AudioRecorder",
    "WebSocketClient",
    "WebSocketConfig",
    "ConnectionState",
    "SessionDB",
]
