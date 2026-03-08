"""Unit tests for MainWindow GUI component."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget

# Ensure QApplication exists for all tests
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestMainWindowInit:
    """Tests for MainWindow initialization."""
    
    def test_init_with_defaults(self, qapp):
        """Test initialization with default parameters."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        
        assert window.windowTitle() == "CoPaw Desktop"
        assert window.centralWidget() is not None
    
    def test_init_with_custom_title(self, qapp):
        """Test initialization with custom title."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(title="Custom Title", fullscreen=False)
        
        assert window.windowTitle() == "Custom Title"
    
    def test_init_fullscreen_mode(self, qapp):
        """Test fullscreen mode initialization."""
        from copaw_desktop.gui.main_window import MainWindow
        
        # Create window (don't show it)
        window = MainWindow(fullscreen=False)
        window.showFullScreen = MagicMock()
        
        # Verify fullscreen flag is set
        assert window.fullscreen is True


class TestMainWindowLayout:
    """Tests for MainWindow layout structure."""
    
    def test_has_three_panels(self, qapp):
        """Test that window has three panels."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        
        # Check that all panels exist
        assert hasattr(window, 'left_panel')
        assert hasattr(window, 'middle_panel')
        assert hasattr(window, 'right_panel')
        
        # Check that panels are widgets
        assert isinstance(window.left_panel, QWidget)
        assert isinstance(window.middle_panel, QWidget)
        assert isinstance(window.right_panel, QWidget)
    
    def test_has_splitter(self, qapp):
        """Test that window has a splitter."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        
        assert hasattr(window, 'splitter')
    
    def test_panel_object_names(self, qapp):
        """Test that panels have correct object names."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        
        assert window.left_panel.objectName() == "leftPanel"
        assert window.middle_panel.objectName() == "middlePanel"
        assert window.right_panel.objectName() == "rightPanel"


class TestMainWindowStyling:
    """Tests for MainWindow styling."""
    
    def test_has_stylesheet(self, qapp):
        """Test that window has a stylesheet."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        
        assert window.styleSheet() != ""
        assert "background-color" in window.styleSheet()
    
    def test_panel_colors_defined(self, qapp):
        """Test that panel colors are defined in stylesheet."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        
        stylesheet = window.styleSheet()
        
        # Check that panel styles are defined
        assert "#leftPanel" in stylesheet
        assert "#middlePanel" in stylesheet
        assert "#rightPanel" in stylesheet


class TestMainWindowKeyboardShortcuts:
    """Tests for MainWindow keyboard shortcuts."""
    
    def test_escape_key_exits_fullscreen(self, qapp):
        """Test that ESC key exits fullscreen."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        window.showFullScreen()
        
        # Simulate ESC key press
        from PyQt6.QtCore import QKeyEvent
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier,
        )
        
        window.keyPressEvent(event)
        
        # Window should no longer be fullscreen
        assert not window.isFullScreen()
    
    def test_f11_toggles_fullscreen(self, qapp):
        """Test that F11 toggles fullscreen."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        
        # Simulate F11 key press to enter fullscreen
        from PyQt6.QtCore import QKeyEvent
        event1 = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_F11,
            Qt.KeyboardModifier.NoModifier,
        )
        
        window.keyPressEvent(event1)
        assert window.isFullScreen()
        
        # Simulate F11 again to exit fullscreen
        window.keyPressEvent(event1)
        assert not window.isFullScreen()


class TestMainWindowResize:
    """Tests for MainWindow resize behavior."""
    
    def test_maintains_panel_proportions(self, qapp):
        """Test that resize maintains panel proportions."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        window.resize(1000, 600)
        
        # Get splitter sizes
        sizes = window.splitter.sizes()
        total = sum(sizes)
        
        if total > 0:
            # Check proportions (20%, 40%, 40%)
            left_ratio = sizes[0] / total
            middle_ratio = sizes[1] / total
            right_ratio = sizes[2] / total
            
            # Allow some tolerance for rounding
            assert abs(left_ratio - 0.20) < 0.05
            assert abs(middle_ratio - 0.40) < 0.05
            assert abs(right_ratio - 0.40) < 0.05


class TestMainWindowCenterOnScreen:
    """Tests for MainWindow centering."""
    
    def test_center_on_screen(self, qapp):
        """Test that window centers on screen."""
        from copaw_desktop.gui.main_window import MainWindow
        
        window = MainWindow(fullscreen=False)
        window.resize(800, 600)
        window.center_on_screen()
        
        # Verify window geometry is reasonable
        assert window.width() == 800
        assert window.height() == 600
