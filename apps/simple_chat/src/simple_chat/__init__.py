"""Simple Chat Application - CoPaw DesktopChannel POC

This is a minimal chat application to demonstrate and verify
CoPaw's DesktopChannel functionality.
"""

__version__ = "0.1.0"
__author__ = "AgentScope Team"

from simple_chat.chat_window import ChatWindow
from simple_chat.channel_client import DesktopChannelClient

__all__ = ["ChatWindow", "DesktopChannelClient"]
