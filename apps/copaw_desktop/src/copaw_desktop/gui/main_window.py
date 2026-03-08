"""Main window for CoPaw Desktop application.

This module provides the main application window with a 3-column layout
for session list, chat panel, and dynamic content display.
"""
from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QWidget,
    QSplitter,
    QLabel,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with 3-column layout.
    
    Layout structure:
    - Left panel (20%): Session list with hourly grouping
    - Middle panel (40%): Chat interface with message bubbles
    - Right panel (40%): Dynamic content (images, charts, markdown)
    
    Example:
        app = QApplication([])
        window = MainWindow()
        window.show()
        app.exec()
    """
    
    def __init__(
        self,
        title: str = "CoPaw Desktop",
        fullscreen: bool = True,
    ) -> None:
        """Initialize main window.
        
        Args:
            title: Window title.
            fullscreen: Whether to start in fullscreen mode.
        """
        super().__init__()
        
        self.title = title
        self.fullscreen = fullscreen
        
        # Initialize UI
        self._setup_window()
        self._setup_ui()
        self._setup_styles()
        
        logger.info(f"MainWindow initialized (fullscreen={fullscreen})")
    
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(self.title)
        
        if self.fullscreen:
            self.showFullScreen()
        else:
            # Default window size for development
            self.resize(1280, 720)
            self.center_on_screen()
    
    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setChildrenCollapsible(False)
        
        # Create placeholder panels
        self.left_panel = self._create_left_panel()
        self.middle_panel = self._create_middle_panel()
        self.right_panel = self._create_right_panel()
        
        # Add panels to splitter
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.middle_panel)
        splitter.addWidget(self.right_panel)
        
        # Set initial sizes (20%, 40%, 40%)
        # These will be recalculated on resize
        splitter.setSizes([200, 400, 400])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Store splitter reference
        self.splitter = splitter
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel for session list.
        
        Returns:
            Left panel widget.
        """
        panel = QWidget()
        panel.setObjectName("leftPanel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder label
        label = QLabel("Session List")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("panelPlaceholder")
        layout.addWidget(label)
        
        return panel
    
    def _create_middle_panel(self) -> QWidget:
        """Create middle panel for chat interface.
        
        Returns:
            Middle panel widget.
        """
        panel = QWidget()
        panel.setObjectName("middlePanel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder label
        label = QLabel("Chat Panel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("panelPlaceholder")
        layout.addWidget(label)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel for dynamic content.
        
        Returns:
            Right panel widget.
        """
        panel = QWidget()
        panel.setObjectName("rightPanel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder label
        label = QLabel("Dynamic Panel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("panelPlaceholder")
        layout.addWidget(label)
        
        return panel
    
    def _setup_styles(self) -> None:
        """Apply stylesheet to window and widgets."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            
            QWidget#leftPanel {
                background-color: #252526;
                border-right: 1px solid #3e3e42;
            }
            
            QWidget#middlePanel {
                background-color: #1e1e1e;
            }
            
            QWidget#rightPanel {
                background-color: #252526;
                border-left: 1px solid #3e3e42;
            }
            
            QLabel#panelPlaceholder {
                color: #858585;
                font-size: 14px;
                font-weight: bold;
            }
            
            QSplitter::handle {
                background-color: #3e3e42;
            }
            
            QSplitter::handle:hover {
                background-color: #0078d4;
            }
        """)
    
    def center_on_screen(self) -> None:
        """Center window on screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.geometry()
            
            x = (screen_geometry.width() - window_geometry.width()) // 2
            y = (screen_geometry.height() - window_geometry.height()) // 2
            
            self.move(x, y)
    
    def resizeEvent(self, event) -> None:
        """Handle window resize to maintain panel proportions.
        
        Args:
            event: Resize event.
        """
        super().resizeEvent(event)
        
        # Maintain 20-40-40 ratio
        if hasattr(self, 'splitter'):
            total_width = self.width()
            left_width = int(total_width * 0.20)
            middle_width = int(total_width * 0.40)
            right_width = total_width - left_width - middle_width
            
            self.splitter.setSizes([left_width, middle_width, right_width])
    
    def keyPressEvent(self, event) -> None:
        """Handle key press events.
        
        Args:
            event: Key press event.
        """
        # ESC to exit fullscreen
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
            logger.debug("Exited fullscreen mode")
        # F11 to toggle fullscreen
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
                logger.debug("Exited fullscreen mode")
            else:
                self.showFullScreen()
                logger.debug("Entered fullscreen mode")
        else:
            super().keyPressEvent(event)
