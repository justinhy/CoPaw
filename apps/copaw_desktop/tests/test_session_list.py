"""Unit tests for SessionListWidget GUI component."""

import sys
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem

from copaw_desktop.core.database import SessionDB
from copaw_desktop.gui.session_list import SessionListWidget


# Ensure QApplication exists for all tests
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def mock_session_db():
    """Create mock session database."""
    db = MagicMock(spec=SessionDB)
    
    # Mock grouped sessions data
    today = date.today()
    
    grouped_data = {
        today: {
            14: [
                {
                    "id": "session-1",
                    "title": "Morning Chat",
                    "started_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
                {
                    "id": "session-2",
                    "title": "Late Morning",
                    "started_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
            ],
            10: [
                {
                    "id": "session-3",
                    "title": "Early Chat",
                    "started_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
            ],
        },
        date(today.year, today.month, today.day - 1): {
            16: [
                {
                    "id": "session-4",
                    "title": "Yesterday Afternoon",
                    "started_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
            ],
        },
    }
    
    db.get_sessions_grouped_by_hour.return_value = grouped_data
    
    return db


class TestSessionListWidgetInit:
    """Tests for SessionListWidget initialization."""
    
    def test_init_without_db(self, qapp):
        """Test initialization without session database."""
        widget = SessionListWidget()
        
        assert widget.session_db is None
        assert widget.tree is not None
        assert widget.tree.topLevelItemCount() == 0
    
    def test_init_with_db(self, qapp, mock_session_db):
        """Test initialization with session database."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        assert widget.session_db == mock_session_db
        # Should have loaded data
        assert widget.tree.topLevelItemCount() > 0


class TestSessionListWidgetRefresh:
    """Tests for SessionListWidget refresh functionality."""
    
    def test_refresh_loads_data(self, qapp, mock_session_db):
        """Test that refresh loads data from database."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        # Clear tree
        widget.tree.clear()
        assert widget.tree.topLevelItemCount() == 0
        
        # Refresh
        widget.refresh()
        
        # Should have data now
        assert widget.tree.topLevelItemCount() > 0
        mock_session_db.get_sessions_grouped_by_hour.assert_called()
    
    def test_refresh_without_db(self, qapp):
        """Test refresh without database does nothing."""
        widget = SessionListWidget()
        
        # Should not raise error
        widget.refresh()
        
        assert widget.tree.topLevelItemCount() == 0
    
    def test_refresh_clears_old_data(self, qapp, mock_session_db):
        """Test that refresh clears old data before loading."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        initial_count = widget.tree.topLevelItemCount()
        
        # Add a dummy item
        dummy = QTreeWidgetItem(["Dummy"])
        widget.tree.addTopLevelItem(dummy)
        
        assert widget.tree.topLevelItemCount() == initial_count + 1
        
        # Refresh should clear it
        widget.refresh()
        
        assert widget.tree.topLevelItemCount() == initial_count


class TestSessionListWidgetHierarchy:
    """Tests for SessionListWidget tree hierarchy."""
    
    def test_date_hour_session_hierarchy(self, qapp, mock_session_db):
        """Test that sessions are organized by date -> hour -> session."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        # Should have date items at top level
        date_count = widget.tree.topLevelItemCount()
        assert date_count > 0
        
        # First date should have hour children
        first_date = widget.tree.topLevelItem(0)
        assert first_date is not None
        
        hour_count = first_date.childCount()
        assert hour_count > 0
        
        # First hour should have session children
        first_hour = first_date.child(0)
        assert first_hour is not None
        
        session_count = first_hour.childCount()
        assert session_count > 0
    
    def test_date_item_type(self, qapp, mock_session_db):
        """Test that date items have correct type data."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        first_date = widget.tree.topLevelItem(0)
        item_type = first_date.data(0, Qt.ItemDataRole.UserRole)
        
        assert item_type == "date"
    
    def test_hour_item_type(self, qapp, mock_session_db):
        """Test that hour items have correct type data."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        first_date = widget.tree.topLevelItem(0)
        first_hour = first_date.child(0)
        
        item_type = first_hour.data(0, Qt.ItemDataRole.UserRole)
        
        assert item_type == "hour"
    
    def test_session_item_type(self, qapp, mock_session_db):
        """Test that session items have correct type and ID."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        first_date = widget.tree.topLevelItem(0)
        first_hour = first_date.child(0)
        first_session = first_hour.child(0)
        
        item_type = first_session.data(0, Qt.ItemDataRole.UserRole)
        session_id = first_session.data(0, Qt.ItemDataRole.UserRole + 1)
        
        assert item_type == "session"
        assert session_id.startswith("session-")


class TestSessionListWidgetSignals:
    """Tests for SessionListWidget signals."""
    
    def test_session_selected_signal(self, qapp, mock_session_db, qtbot):
        """Test that clicking a session emits session_selected signal."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        # Find a session item
        first_date = widget.tree.topLevelItem(0)
        first_hour = first_date.child(0)
        first_session = first_hour.child(0)
        
        # Connect signal spy
        with qtbot.waitSignal(widget.session_selected, timeout=1000) as blocker:
            # Simulate click
            widget.tree.itemClicked.emit(first_session, 0)
        
        # Check signal was emitted with session ID
        assert len(blocker.args) == 1
        session_id = blocker.args[0]
        assert session_id.startswith("session-")
    
    def test_date_click_no_signal(self, qapp, mock_session_db, qtbot):
        """Test that clicking a date item doesn't emit signal."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        first_date = widget.tree.topLevelItem(0)
        
        # Signal should not be emitted
        with qtbot.assertNotEmitted(widget.session_selected):
            widget.tree.itemClicked.emit(first_date, 0)
    
    def test_hour_click_no_signal(self, qapp, mock_session_db, qtbot):
        """Test that clicking an hour item doesn't emit signal."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        first_date = widget.tree.topLevelItem(0)
        first_hour = first_date.child(0)
        
        # Signal should not be emitted
        with qtbot.assertNotEmitted(widget.session_selected):
            widget.tree.itemClicked.emit(first_hour, 0)


class TestSessionListWidgetMethods:
    """Tests for SessionListWidget utility methods."""
    
    def test_get_selected_session_id(self, qapp, mock_session_db):
        """Test getting selected session ID."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        # Select a session
        first_date = widget.tree.topLevelItem(0)
        first_hour = first_date.child(0)
        first_session = first_hour.child(0)
        
        widget.tree.setCurrentItem(first_session)
        
        session_id = widget.get_selected_session_id()
        
        assert session_id is not None
        assert session_id.startswith("session-")
    
    def test_get_selected_session_id_no_selection(self, qapp, mock_session_db):
        """Test getting selected session ID when nothing is selected."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        # Nothing selected
        widget.tree.clearSelection()
        
        session_id = widget.get_selected_session_id()
        
        assert session_id is None
    
    def test_expand_all(self, qapp, mock_session_db):
        """Test expand_all method."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        # Collapse all first
        widget.collapse_all()
        
        # Expand all
        widget.expand_all()
        
        # Check that items are expanded
        first_date = widget.tree.topLevelItem(0)
        assert first_date.isExpanded()
    
    def test_collapse_all(self, qapp, mock_session_db):
        """Test collapse_all method."""
        widget = SessionListWidget(session_db=mock_session_db)
        
        # Expand all first
        widget.expand_all()
        
        # Collapse all
        widget.collapse_all()
        
        # Check that items are collapsed
        first_date = widget.tree.topLevelItem(0)
        assert not first_date.isExpanded()
    
    def test_set_session_db(self, qapp, mock_session_db):
        """Test setting session database."""
        widget = SessionListWidget()
        
        assert widget.session_db is None
        
        widget.set_session_db(mock_session_db)
        
        assert widget.session_db == mock_session_db
        # Should have refreshed automatically
        mock_session_db.get_sessions_grouped_by_hour.assert_called()
