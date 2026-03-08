"""GUI components for CoPaw Desktop application.

This package contains all graphical user interface components including
the main window, panels, and widgets.
"""

from copaw_desktop.gui.main_window import MainWindow
from copaw_desktop.gui.session_list import SessionListWidget
from copaw_desktop.gui.chat_panel import ChatPanelWidget, MessageBubble
from copaw_desktop.gui.dynamic_panel import DynamicPanelWidget
from copaw_desktop.gui.chart_widget import ChartWidget

__all__ = [
    "MainWindow",
    "SessionListWidget",
    "ChatPanelWidget",
    "MessageBubble",
    "DynamicPanelWidget",
    "ChartWidget",
]
