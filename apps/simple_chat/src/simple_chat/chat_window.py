"""Simple chat window for CoPaw DesktopChannel POC.

This module provides a simple PyQt6 chat window
for testing CoPaw's DesktopChannel functionality.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
)

from .channel_client import DesktopChannelClient

logger = logging.getLogger(__name__)


class ChatWindow(QWidget):
    """Simple chat window for testing DesktopChannel.
    
    Features:
    - Message input and display
    - Connection status indicator
    - Send/Receive messages via DesktopChannel
    """
    
    # Signals
    message_sent = pyqtSignal(str)  # Emitted when user sends message
    message_received = pyqtSignal(dict)  # Emitted when message received
    
    def __init__(self, ws_url: str = "ws://127.0.0.1:8088/desktop/ws") -> None:
        """Initialize chat window.
        
        Args:
            ws_url: WebSocket URL for DesktopChannel.
        """
        super().__init__()
        
        self.ws_url = ws_url
        self._client: Optional[DesktopChannelClient] = None
        
        self._setup_ui()
        self._setup_styles()
        
        logger.info("ChatWindow initialized")
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Status bar
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._toggle_connection)
        status_layout.addWidget(self.connect_button)
        
        layout.addLayout(status_layout)
        
        # Chat display
        self.chat_display = QLabel()
        self.chat_display.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.chat_display.setWordWrap(True)
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setMinimumHeight(300)
        
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.setMaximumHeight(100)
        self.message_input.setObjectName("messageInput")
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._send_message)
        self.send_button.setEnabled(False)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Set layout
        self.setLayout(layout)
    
    def _setup_styles(self) -> None:
        """Apply stylesheet."""
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
            
            QLabel#statusLabel {
                color: #666666;
                font-weight: bold;
                padding: 5px;
            }
            
            QLabel#chatDisplay {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
            }
            
            QTextEdit#messageInput {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #005a9e;
            }
            
            QPushButton:pressed {
                background-color: #004578;
            }
            
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
    
    def _toggle_connection(self) -> None:
        """Toggle connection to DesktopChannel."""
        if self._client and self._client.is_connected():
            asyncio.create_task(self._disconnect())
        else:
            asyncio.create_task(self._connect())
    
    async def _connect(self) -> None:
        """Connect to DesktopChannel."""
        self.status_label.setText("Connecting...")
        self.connect_button.setEnabled(False)
        
        try:
            # Create client
            self._client = DesktopChannelClient(
                ws_url=self.ws_url,
                on_message=self._on_message_received,
                on_error=self._on_error,
            )
            
            # Connect
            success = await self._client.connect()
            
            if success:
                self.status_label.setText("Connected")
                self.status_label.setStyleSheet("color: #28a745;")
                self.connect_button.setText("Disconnect")
                self.connect_button.setEnabled(True)
                self.send_button.setEnabled(True)
                
                self._append_message("System", "Connected to CoPaw!")
            else:
                self.status_label.setText("Connection Failed")
                self.status_label.setStyleSheet("color: #dc3545;")
                self.connect_button.setEnabled(True)
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545;")
            self.connect_button.setEnabled(True)
    
    async def _disconnect(self) -> None:
        """Disconnect from DesktopChannel."""
        if self._client:
            await self._client.disconnect()
            self._client = None
        
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: #666666;")
        self.connect_button.setText("Connect")
        self.connect_button.setEnabled(True)
        self.send_button.setEnabled(False)
        
        self._append_message("System", "Disconnected from CoPaw")
    
    def _send_message(self) -> None:
        """Send message to DesktopChannel."""
        text = self.message_input.toPlainText().strip()
        
        if not text:
            return
        
        if not self._client or not self._client.is_connected():
            logger.warning("Not connected to DesktopChannel")
            return
        
        # Send asynchronously
        asyncio.create_task(self._send_message_async(text))
        
        # Clear input
        self.message_input.clear()
    
    async def _send_message_async(self, text: str) -> None:
        """Send message asynchronously.
        
        Args:
            text: Message text to send.
        """
        success = await self._client.send_text(text)
        
        if success:
            self._append_message("You", text)
            self.message_sent.emit(text)
        else:
            self._append_message("System", "Failed to send message")
    
    def _on_message_received(self, message: dict) -> None:
        """Handle received message from DesktopChannel.
        
        Args:
            message: Received message dictionary.
        """
        msg_type = message.get("type", "unknown")
        content = message.get("content", str(message))
        
        self._append_message("CoPaw", content)
        self.message_received.emit(message)
    
    def _on_error(self, error: Exception) -> None:
        """Handle error from DesktopChannel.
        
        Args:
            error: Error exception.
        """
        logger.error(f"DesktopChannel error: {error}")
        self._append_message("Error", str(error))
    
    def _append_message(self, sender: str, text: str) -> None:
        """Append message to chat display.
        
        Args:
            sender: Message sender (You/CoPaw/System/Error).
            text: Message text.
        """
        current_text = self.chat_display.text()
        
        if current_text:
            new_text = f"{current_text}\n\n{sender}: {text}"
        else:
            new_text = f"{sender}: {text}"
        
        self.chat_display.setText(new_text)
    
    def keyPressEvent(self, event) -> None:
        """Handle key press events.
        
        Args:
            event: Key event.
        """
        # Enter to send message
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._send_message()
                event.accept()
                return
        
        super().keyPressEvent(event)
    
    def closeEvent(self, event) -> None:
        """Handle window close event.
        
        Args:
            event: Close event.
        """
        # Disconnect before closing
        if self._client and self._client.is_connected():
            asyncio.create_task(self._disconnect())
        
        event.accept()
