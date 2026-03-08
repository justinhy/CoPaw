"""Chart widget for displaying interactive charts.

This module provides a chart visualization widget using ECharts
for rendering interactive charts and graphs.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

logger = logging.getLogger(__name__)

# Try to import QWebEngineView
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    logger.warning(
        "QWebEngineView not available. "
        "Install PyQt6-WebEngine for chart support."
    )


class ChartWidget(QWidget):
    """Widget for displaying interactive charts using ECharts.
    
    Supports various chart types including:
    - Line charts
    - Bar charts
    - Pie charts
    - Scatter plots
    - And more...
    
    Example:
        widget = ChartWidget()
        option = {
            "title": {"text": "Sales Data"},
            "xAxis": {"type": "category", "data": ["Mon", "Tue"]},
            "yAxis": {"type": "value"},
            "series": [{"type": "bar", "data": [120, 200]}]
        }
        widget.render_chart(option)
    """
    
    # Signal emitted when chart is rendered
    chart_rendered = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize chart widget.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._setup_ui()
        
        logger.debug("ChartWidget initialized")
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if WEBENGINE_AVAILABLE:
            # Create web engine view
            self.web_view = QWebEngineView()
            
            # Load ECharts HTML template
            html_content = self._get_echarts_html()
            self.web_view.setHtml(html_content, QUrl("about:blank"))
            
            layout.addWidget(self.web_view)
        else:
            # Fallback: show placeholder
            from PyQt6.QtWidgets import QLabel
            placeholder = QLabel("Chart (WebEngine not available)")
            placeholder.setAlignment(0x84)  # Qt.AlignCenter
            placeholder.setStyleSheet("""
                QLabel {
                    color: #858585;
                    font-size: 14px;
                }
            """)
            layout.addWidget(placeholder)
            self.web_view = None
    
    def _get_echarts_html(self) -> str:
        """Get HTML template with ECharts.
        
        Returns:
            HTML content with ECharts library.
        """
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
        }
        #chart {
            width: 100%;
            height: 100vh;
        }
    </style>
</head>
<body>
    <div id="chart"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <script>
        var chart = echarts.init(document.getElementById('chart'), 'dark');
        
        window.renderChart = function(option) {
            try {
                chart.setOption(option, true);
            } catch (e) {
                console.error('Chart render error:', e);
            }
        };
        
        window.resizeChart = function() {
            chart.resize();
        };
        
        // Resize on window resize
        window.addEventListener('resize', function() {
            chart.resize();
        });
    </script>
</body>
</html>
        """
    
    def render_chart(self, option: dict) -> bool:
        """Render chart with ECharts option.
        
        Args:
            option: ECharts option dictionary.
        
        Returns:
            True if chart rendered successfully.
        """
        if not self.web_view:
            logger.warning("WebEngine not available, cannot render chart")
            return False
        
        try:
            # Convert option to JSON
            option_json = json.dumps(option)
            
            # Inject JavaScript to render chart
            js_code = f"renderChart({option_json});"
            self.web_view.page().runJavaScript(js_code)
            
            logger.debug("Chart rendered successfully")
            self.chart_rendered.emit()
            return True
        
        except Exception as e:
            logger.error(f"Failed to render chart: {e}")
            return False
    
    def clear_chart(self) -> None:
        """Clear current chart."""
        if not self.web_view:
            return
        
        try:
            self.web_view.page().runJavaScript("renderChart({});")
            logger.debug("Chart cleared")
        except Exception as e:
            logger.error(f"Failed to clear chart: {e}")
    
    def resize_chart(self) -> None:
        """Resize chart to fit widget."""
        if not self.web_view:
            return
        
        try:
            self.web_view.page().runJavaScript("resizeChart();")
            logger.debug("Chart resized")
        except Exception as e:
            logger.error(f"Failed to resize chart: {e}")
    
    def resizeEvent(self, event) -> None:
        """Handle widget resize.
        
        Args:
            event: Resize event.
        """
        super().resizeEvent(event)
        self.resize_chart()
