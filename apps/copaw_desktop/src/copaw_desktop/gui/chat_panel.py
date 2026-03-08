"""Chat panel widget for displaying message bubbles.

This module provides the chat interface with message bubbles for user
and assistant messages, including streaming text support.
"""
from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
)

logger = logging.getLogger(__name__)


class MessageBubble(QFrame):
    """Message bubble widget for displaying a single message.
    
    Supports different styles for user and assistant messages.
    
    Attributes:
        role: Message role ("user" or "assistant").
        content: Message text content.
    """
    
    def __init__(
        self,
        role: str,
        content: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize message bubble.
        
        Args:
            role: Message role ("user" or "assistant").
            content: Message text content.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.role = role
        self._content = content
        
        self._setup_ui()
        self._apply_style()
        
        if content:
            self.set_content(content)
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Role label
        self.role_label = QLabel(self.role.capitalize())
        self.role_label.setObjectName("roleLabel")
        layout.addWidget(self.role_label)
        
        # Content label
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.content_label.setObjectName("contentLabel")
        layout.addWidget(self.content_label)
    
    def _apply_style(self) -> None:
        """Apply stylesheet based on role."""
        if self.role == "user":
            self.setObjectName("userBubble")
            self.setStyleSheet("""
                #userBubble {
                    background-color: #0078d4;
                    border-radius: 8px;
                    margin-left: 40px;
                    margin-right: 8px;
                }
                #roleLabel {
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 11px;
                }
                #contentLabel {
                    color: #ffffff;
                    font-size: 14px;
                }
            """)
        else:  # assistant
            self.setObjectName("assistantBubble")
            self.setStyleSheet("""
                #assistantBubble {
                    background-color: #2d2d30;
                    border-radius: 8px;
                    margin-left: 8px;
                    margin-right: 40px;
                }
                #roleLabel {
                    color: #858585;
                    font-weight: bold;
                    font-size: 11px;
                }
                #contentLabel {
                    color: #d4d4d4;
                    font-size: 14px;
                }
            """)
    
    def set_content(self, content: str) -> None:
        """Set message content.
        
        Args:
            content: Message text.
        """
        self._content = content
        self.content_label.setText(content)
    
    def append_content(self, text: str) -> None:
        """Append text to existing content.
        
        Args:
            text: Text to append.
        """
        self._content += text
        self.content_label.setText(self._content)


class ChatPanelWidget(QWidget):
    """Widget for displaying chat messages with bubbles.
    
    Features:
    - Scrollable message list
    - User and assistant message bubbles
    - Streaming text support
    - Auto-scroll to bottom
    
    Example:
        widget = ChatPanelWidget()
        widget.add_message("user", "Hello!")
        widget.add_message("assistant", "Hi there!")
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize chat panel widget.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._bubbles: list[MessageBubble] = []
        self._current_streaming_bubble: Optional[MessageBubble] = None
        
        self._setup_ui()
        
        logger.debug("ChatPanelWidget initialized")
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setObjectName("chatScrollArea")
        
        # Container widget for messages
        self.container = QWidget()
        self.container.setObjectName("chatContainer")
        
        # Container layout
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(12)
        self.layout.addStretch()  # Push messages to top
        
        # Set container as scroll area widget
        self.scroll_area.setWidget(self.container)
        
        # Add scroll area to main layout
        main_layout.addWidget(self.scroll_area)
        
        # Apply stylesheet
        self.setStyleSheet("""
            #chatScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            #chatContainer {
                background-color: #1e1e1e;
            }
        """)
    
    def add_message(
        self,
        role: str,
        content: str,
    ) -> MessageBubble:
        """Add a message bubble to the chat.
        
        Args:
            role: Message role ("user" or "assistant").
            content: Message text.
        
        Returns:
            Created message bubble.
        """
        # Create bubble
        bubble = MessageBubble(role, content)
        
        # Insert before stretch
        self.layout.insertWidget(self.layout.count() - 1, bubble)
        
        # Track bubble
        self._bubbles.append(bubble)
        
        # Scroll to bottom
        self._scroll_to_bottom()
        
        logger.debug(f"Added {role} message: {content[:50]}...")
        
        return bubble
    
    def start_streaming_message(self, role: str = "assistant") -> MessageBubble:
        """Start a streaming message bubble.
        
        Args:
            role: Message role (default: "assistant").
        
        Returns:
            Created streaming bubble.
        """
        # Create empty bubble
        bubble = MessageBubble(role, "")
        
        # Insert before stretch
        self.layout.insertWidget(self.layout.count() - 1, bubble)
        
        # Track as current streaming bubble
        self._current_streaming_bubble = bubble
        self._bubbles.append(bubble)
        
        # Scroll to bottom
        self._scroll_to_bottom()
        
        logger.debug(f"Started streaming {role} message")
        
        return bubble
    
    def append_to_streaming(self, text: str) -> None:
        """Append text to current streaming bubble.
        
        Args:
            text: Text to append.
        """
        if self._current_streaming_bubble:
            self._current_streaming_bubble.append_content(text)
            self._scroll_to_bottom()
    
    def finish_streaming(self) -> None:
        """Finish current streaming message."""
        if self._current_streaming_bubble:
            logger.debug(
                f"Finished streaming message: "
                f"{self._current_streaming_bubble._content[:50]}..."
            )
            self._current_streaming_bubble = None
    
    def clear_messages(self) -> None:
        """Clear all messages from the chat."""
        # Remove all bubbles
        for bubble in self._bubbles:
            bubble.deleteLater()
        
        self._bubbles.clear()
        self._current_streaming_bubble = None
        
        logger.debug("Cleared all messages")
    
    def _scroll_to_bottom(self) -> None:
        """Scroll to bottom of chat."""
        # Use QTimer to ensure scroll happens after layout update
        QTimer.singleShot(10, self._do_scroll)
    
    def _do_scroll(self) -> None:
        """Perform the actual scroll."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def get_message_count(self) -> int:
        """Get total number of messages.
        
        Returns:
            Message count.
        """
        return len(self._bubbles)
