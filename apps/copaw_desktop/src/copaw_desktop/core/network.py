"""Network communication module."""

from typing import Callable, Optional


class WebSocketClient:
    """Placeholder for WebSocketClient - to be implemented in feat-002."""

    def __init__(self, url: str) -> None:
        """Initialize WebSocketClient.

        Args:
            url: WebSocket server URL.
        """
        self.url = url

    async def connect(self) -> bool:
        """Connect to WebSocket server.

        Returns:
            True if connected successfully.
        """
        return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        pass

    async def send(self, message: dict) -> None:
        """Send message to server.

        Args:
            message: Message dictionary to send.
        """
        pass

    def on_message(self, callback: Callable) -> None:
        """Register message callback.

        Args:
            callback: Function to call when message received.
        """
        pass
