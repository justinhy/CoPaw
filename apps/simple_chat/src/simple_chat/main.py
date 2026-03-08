"""Main entry point for Simple Chat application.

This is a minimal chat application to demonstrate and verify
CoPaw's DesktopChannel functionality.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from .chat_window import ChatWindow

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path.home() / ".simple_chat" / "logs" / "chat.log",
            mode='a',
            encoding='utf-8',
        ),
    ],
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for Simple Chat.
    
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    try:
        # Ensure log directory exists
        log_dir = Path.home() / ".simple_chat" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Starting Simple Chat...")
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Simple Chat")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("AgentScope")
        
        # Create and show chat window
        window = ChatWindow()
        window.setWindowTitle("Simple Chat - CoPaw DesktopChannel POC")
        window.resize(600, 500)
        window.show()
        
        logger.info("Application initialized successfully")
        
        # Run event loop
        return app.exec()
    
    except Exception as e:
        logger.exception(f"Application failed to start: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
