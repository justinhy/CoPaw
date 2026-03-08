#!/usr/bin/env python3
"""CoPaw Desktop - Main Application Entry Point.

This module provides the application entry point and initialization logic.
"""

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

# Set up logging
log_dir = Path.home() / ".copaw_desktop" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            log_dir / "desktop.log",
            mode='a',
            encoding='utf-8',
        ),
    ],
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for CoPaw Desktop application.
    
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    try:
        logger.info("Starting CoPaw Desktop...")
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("CoPaw Desktop")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("AgentScope")
        
        # Import here to avoid circular imports
        from copaw_desktop.gui.main_window import MainWindow
        
        # Create and show main window
        window = MainWindow(
            title="CoPaw Desktop",
            fullscreen=True,
        )
        window.show()
        
        logger.info("Application initialized successfully")
        
        # Run event loop
        return app.exec()
    
    except Exception as e:
        logger.exception(f"Application failed to start: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
