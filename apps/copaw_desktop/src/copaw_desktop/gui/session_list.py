"""Session list widget for displaying chat sessions.

This module provides a tree widget for displaying chat sessions grouped
by date and hour, allowing users to navigate their conversation history.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from copaw_desktop.core.database import SessionDB

logger = logging.getLogger(__name__)


class SessionListWidget(QWidget):
    """Widget for displaying session list with hourly grouping.
    
    Displays sessions in a hierarchical tree structure:
    - Date (e.g., "2026-03-08")
      - Hour (e.g., "14:00")
        - Session (e.g., "My Chat Session")
    
    Signals:
        session_selected: Emitted when a session is clicked.
                         Argument: session_id (str)
    
    Example:
        widget = SessionListWidget(session_db)
        widget.session_selected.connect(self.on_session_selected)
    """
    
    # Signal emitted when a session is selected
    session_selected = pyqtSignal(str)  # session_id
    
    def __init__(
        self,
        session_db: Optional["SessionDB"] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize session list widget.
        
        Args:
            session_db: Session database instance.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.session_db = session_db
        
        # Set up UI
        self._setup_ui()
        self._setup_connections()
        
        # Load initial data
        if self.session_db:
            self.refresh()
        
        logger.debug("SessionListWidget initialized")
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setObjectName("sessionTree")
        
        # Set column count
        self.tree.setColumnCount(1)
        
        # Add to layout
        layout.addWidget(self.tree)
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        self.tree.itemClicked.connect(self._on_item_clicked)
    
    def refresh(self) -> None:
        """Refresh session list from database."""
        if not self.session_db:
            logger.warning("No session database configured")
            return
        
        # Clear existing items
        self.tree.clear()
        
        # Get grouped sessions
        grouped = self.session_db.get_sessions_grouped_by_hour()
        
        if not grouped:
            logger.debug("No sessions to display")
            return
        
        # Build tree structure
        for session_date, hour_dict in sorted(
            grouped.items(),
            key=lambda x: x[0],
            reverse=True,  # Most recent first
        ):
            # Create date item
            date_item = self._create_date_item(session_date)
            self.tree.addTopLevelItem(date_item)
            
            # Add hour items under date
            for hour, sessions in sorted(
                hour_dict.items(),
                key=lambda x: x[0],
                reverse=True,  # Most recent hour first
            ):
                hour_item = self._create_hour_item(hour)
                date_item.addChild(hour_item)
                
                # Add session items under hour
                for session in sessions:
                    session_item = self._create_session_item(session)
                    hour_item.addChild(session_item)
            
            # Expand first date by default
            if self.tree.topLevelItem(0) == date_item:
                date_item.setExpanded(True)
        
        logger.debug(f"Refreshed session list: {len(grouped)} dates")
    
    def _create_date_item(self, session_date: date) -> QTreeWidgetItem:
        """Create a date tree item.
        
        Args:
            session_date: Date for this item.
        
        Returns:
            Date tree item.
        """
        # Format date as "YYYY-MM-DD" or "Today" if today
        today = date.today()
        
        if session_date == today:
            text = "Today"
        elif session_date == date(today.year, today.month, today.day - 1):
            text = "Yesterday"
        else:
            text = session_date.strftime("%Y-%m-%d")
        
        item = QTreeWidgetItem([text])
        item.setData(0, Qt.ItemDataRole.UserRole, "date")
        item.setData(0, Qt.ItemDataRole.UserRole + 1, session_date.isoformat())
        
        return item
    
    def _create_hour_item(self, hour: int) -> QTreeWidgetItem:
        """Create an hour tree item.
        
        Args:
            hour: Hour (0-23).
        
        Returns:
            Hour tree item.
        """
        text = f"{hour:02d}:00"
        
        item = QTreeWidgetItem([text])
        item.setData(0, Qt.ItemDataRole.UserRole, "hour")
        item.setData(0, Qt.ItemDataRole.UserRole + 1, hour)
        
        return item
    
    def _create_session_item(self, session: Dict) -> QTreeWidgetItem:
        """Create a session tree item.
        
        Args:
            session: Session dictionary with 'id', 'title', etc.
        
        Returns:
            Session tree item.
        """
        # Use title or "Untitled" if no title
        title = session.get("title") or "Untitled"
        started_at = session.get("started_at", "")
        
        # Format time from started_at if available
        if started_at:
            try:
                dt = datetime.fromisoformat(started_at)
                time_str = dt.strftime("%H:%M")
                text = f"{time_str} - {title}"
            except Exception:
                text = title
        else:
            text = title
        
        item = QTreeWidgetItem([text])
        item.setData(0, Qt.ItemDataRole.UserRole, "session")
        item.setData(0, Qt.ItemDataRole.UserRole + 1, session.get("id", ""))
        
        # Add tooltip with full info
        tooltip = f"Session: {title}\nStarted: {started_at}"
        item.setToolTip(0, tooltip)
        
        return item
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click event.
        
        Args:
            item: Clicked item.
            column: Clicked column.
        """
        # Only emit signal for session items
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_type == "session":
            session_id = item.data(0, Qt.ItemDataRole.UserRole + 1)
            
            if session_id:
                logger.debug(f"Session selected: {session_id}")
                self.session_selected.emit(session_id)
    
    def set_session_db(self, session_db: "SessionDB") -> None:
        """Set session database and refresh.
        
        Args:
            session_db: Session database instance.
        """
        self.session_db = session_db
        self.refresh()
    
    def get_selected_session_id(self) -> Optional[str]:
        """Get currently selected session ID.
        
        Returns:
            Session ID if a session is selected, None otherwise.
        """
        item = self.tree.currentItem()
        
        if item:
            item_type = item.data(0, Qt.ItemDataRole.UserRole)
            
            if item_type == "session":
                return item.data(0, Qt.ItemDataRole.UserRole + 1)
        
        return None
    
    def expand_all(self) -> None:
        """Expand all tree items."""
        self.tree.expandAll()
    
    def collapse_all(self) -> None:
        """Collapse all tree items."""
        self.tree.collapseAll()
