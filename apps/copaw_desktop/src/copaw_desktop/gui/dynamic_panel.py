"""Dynamic panel widget for displaying images and markdown.

This module provides a right panel for dynamic content display
including images, charts, and markdown documents.
"""
from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class ImagePreviewWidget(QWidget):
    """Widget for displaying images.
    
    Supports loading images from URLs or local paths.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize image preview widget.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setObjectName("imageLabel")
        
        layout.addWidget(self.image_label)
    
    def load_image(self, image_path: str) -> bool:
        """Load image from path or URL.
        
        Args:
            image_path: Local file path or URL.
        
        Returns:
            True if image loaded successfully.
        """
        try:
            if image_path.startswith(("http://", "https://")):
                # TODO: Implement async image download for URLs
                logger.warning(f"URL image loading not implemented: {image_path}")
                return False
            else:
                # Load from local file
                pixmap = QPixmap(image_path)
                
                if pixmap.isNull():
                    logger.error(f"Failed to load image: {image_path}")
                    return False
                
                # Scale to fit while maintaining aspect ratio
                scaled = pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                
                self.image_label.setPixmap(scaled)
                logger.debug(f"Loaded image: {image_path}")
                return True
        
        except Exception as e:
            logger.exception(f"Error loading image: {e}")
            return False
    
    def clear_image(self) -> None:
        """Clear displayed image."""
        self.image_label.clear()


class MarkdownPreviewWidget(QWidget):
    """Widget for displaying markdown content.
    
    Note: This is a simplified implementation using QLabel.
    For full markdown support, consider using QWebEngineView.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize markdown preview widget.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Content label
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.content_label.setOpenExternalLinks(True)
        self.content_label.setObjectName("markdownLabel")
        
        layout.addWidget(self.content_label)
        
        # Apply stylesheet
        self.setStyleSheet("""
            #markdownLabel {
                color: #d4d4d4;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
    
    def set_markdown(self, markdown_text: str) -> None:
        """Set markdown content.
        
        Args:
            markdown_text: Markdown formatted text.
        """
        # Simple markdown to HTML conversion
        # Note: For full support, use a markdown library
        html = self._simple_markdown_to_html(markdown_text)
        self.content_label.setText(html)
        logger.debug(f"Set markdown content: {len(markdown_text)} chars")
    
    def _simple_markdown_to_html(self, text: str) -> str:
        """Convert simple markdown to HTML.
        
        Args:
            text: Markdown text.
        
        Returns:
            HTML formatted text.
        """
        # Very basic conversion - just preserve line breaks
        html = text.replace("\n", "<br>")
        return html
    
    def clear(self) -> None:
        """Clear content."""
        self.content_label.clear()


class DynamicPanelWidget(QWidget):
    """Widget for displaying dynamic content.
    
    Supports switching between different content types:
    - Images
    - Markdown documents
    - Charts (future)
    
    Example:
        panel = DynamicPanelWidget()
        panel.show_image("/path/to/image.png")
        panel.show_markdown("# Hello\\n\\nWorld")
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize dynamic panel widget.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._setup_ui()
        
        logger.debug("DynamicPanelWidget initialized")
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stacked widget for switching content types
        self.stacked_widget = QStackedWidget()
        
        # Create placeholder widget (default)
        self.placeholder = QLabel("Dynamic Content")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setObjectName("dynamicPlaceholder")
        self.placeholder.setStyleSheet("""
            #dynamicPlaceholder {
                color: #858585;
                font-size: 14px;
            }
        """)
        
        # Create content widgets
        self.image_widget = ImagePreviewWidget()
        self.markdown_widget = MarkdownPreviewWidget()
        
        # Add widgets to stack
        self.stacked_widget.addWidget(self.placeholder)
        self.stacked_widget.addWidget(self.image_widget)
        self.stacked_widget.addWidget(self.markdown_widget)
        
        # Add to layout
        layout.addWidget(self.stacked_widget)
    
    def show_image(self, image_path: str) -> bool:
        """Show image in panel.
        
        Args:
            image_path: Path or URL to image.
        
        Returns:
            True if image loaded successfully.
        """
        success = self.image_widget.load_image(image_path)
        
        if success:
            self.stacked_widget.setCurrentWidget(self.image_widget)
        
        return success
    
    def show_markdown(self, markdown_text: str) -> None:
        """Show markdown content in panel.
        
        Args:
            markdown_text: Markdown formatted text.
        """
        self.markdown_widget.set_markdown(markdown_text)
        self.stacked_widget.setCurrentWidget(self.markdown_widget)
    
    def show_placeholder(self) -> None:
        """Show placeholder widget."""
        self.stacked_widget.setCurrentWidget(self.placeholder)
    
    def clear(self) -> None:
        """Clear all content."""
        self.image_widget.clear_image()
        self.markdown_widget.clear()
        self.show_placeholder()
