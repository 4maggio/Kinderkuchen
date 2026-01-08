"""
Day View - Detailed view of a single day's schedule.

Shows weather, three main activity icons, and detailed text entries.
"""

from datetime import date, timedelta
from typing import List, Dict, Optional
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor

from utils.i18n import t
from themes.theme_manager import Theme, ThemeColors


class DayView(QWidget):
    """Day view widget showing detailed schedule for one day."""
    
    def __init__(self, database, current_date: date = None):
        """Initialize day view.
        
        Args:
            database: CalendarDatabase instance
            current_date: Initial date to display
        """
        super().__init__()
        
        self.database = database
        self.current_date = current_date or date.today()
        self.theme_colors = ThemeColors()
        self.icon_font_size = 72
        
        self._init_ui()
        self.refresh()
    
    def _init_ui(self):
        """Initialize the user interface."""
        self.setObjectName("DayView")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Date header with navigation
        header_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(50, 50)
        self.prev_btn.clicked.connect(self._prev_day)
        header_layout.addWidget(self.prev_btn)
        
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setFont(QFont("Arial", 20, QFont.Bold))
        header_layout.addWidget(self.date_label, 1)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(50, 50)
        self.next_btn.clicked.connect(self._next_day)
        header_layout.addWidget(self.next_btn)
        
        layout.addLayout(header_layout)
        
        # Weather section
        self.weather_label = QLabel("☀ 72°F - Clear")
        self.weather_label.setAlignment(Qt.AlignCenter)
        self.weather_label.setFont(QFont("Arial", max(14, int(self.icon_font_size * 0.45))))
        layout.addWidget(self.weather_label)
        
        # Three icon slots
        icons_layout = QHBoxLayout()
        icons_layout.setSpacing(20)
        
        self.icon_widgets = []
        for i in range(3):
            icon_container = self._create_icon_slot(i)
            icons_layout.addWidget(icon_container)
            self.icon_widgets.append(icon_container)
        
        layout.addLayout(icons_layout)
        
        # Schedule details section
        details_label = QLabel("📝 Schedule Details:")
        details_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(details_label)
        
        # Scrollable text area for detailed entries
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.details_widget)
        layout.addWidget(self.scroll_area, 1)
        
        self._apply_theme_styles()
    
    def _create_icon_slot(self, index: int) -> QWidget:
        """Create an icon slot widget.
        
        Args:
            index: Slot index (0-2)
            
        Returns:
            Icon slot widget
        """
        container = QFrame()
        container.setFixedSize(220, 200)
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon placeholder (will be populated with actual icons)
        icon_label = QLabel("📅")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Arial", self.icon_font_size))
        icon_label.setObjectName(f"icon_{index}")
        layout.addWidget(icon_label)
        
        # Activity name
        name_label = QLabel("Free Time")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_label.setObjectName(f"name_{index}")
        layout.addWidget(name_label)
        
        # Time
        time_label = QLabel("")
        time_label.setAlignment(Qt.AlignCenter)
        time_label.setFont(QFont("Arial", 10))
        time_label.setObjectName(f"time_{index}")
        layout.addWidget(time_label)
        
        self._style_icon_slot(container)
        return container

    def apply_theme(self, theme: Optional[Theme]):
        """Apply updated theme colors to the view."""
        self.theme_colors = theme.colors if theme else ThemeColors()
        # Update fonts from theme
        if theme and hasattr(theme, 'font'):
            self.date_label.setFont(QFont(theme.font.family, theme.font.size_xlarge, QFont.Bold))
        self._apply_theme_styles()

    def _apply_theme_styles(self):
        """Update all styles to match the active theme colors."""
        c = self.theme_colors
        self.setStyleSheet(f"""
            QWidget#DayView {{
                background-color: {c.background};
                color: {c.text_primary};
            }}
            QWidget#DayView QLabel {{
                color: {c.text_primary};
            }}
        """)
        self.weather_label.setStyleSheet(
            f"background-color: {c.background_secondary}; padding: 10px; border-radius: 8px;"
        )
        self.scroll_area.setStyleSheet(
            f"QScrollArea {{ border: none; background-color: {c.background_secondary}; border-radius: 8px; }}"
        )
        for icon_slot in getattr(self, 'icon_widgets', []):
            self._style_icon_slot(icon_slot)

    def _style_icon_slot(self, container: QFrame):
        """Apply themed styling to an icon slot container."""
        c = self.theme_colors
        container.setStyleSheet(
            f"QFrame {{ background-color: {c.background_secondary}; border-radius: 10px; padding: 10px; }}"
        )

    def set_calendar_icon_size(self, size: int):
        """Adjust icon and weather label sizes based on appearance settings."""
        try:
            sanitized = int(size)
        except (TypeError, ValueError):
            sanitized = self.icon_font_size
        sanitized = max(24, min(96, sanitized))
        self.icon_font_size = sanitized
        for index, container in enumerate(getattr(self, 'icon_widgets', [])):
            icon_label = container.findChild(QLabel, f"icon_{index}")
            if icon_label:
                font = icon_label.font()
                font.setPointSize(sanitized)
                icon_label.setFont(font)
        if hasattr(self, 'weather_label'):
            weather_font = self.weather_label.font()
            weather_font.setPointSize(max(14, int(self.icon_font_size * 0.45)))
            self.weather_label.setFont(weather_font)
    
    def set_icon_size(self, size: int):
        """Legacy method - delegates to set_calendar_icon_size for compatibility."""
        self.set_calendar_icon_size(size)
    
    def set_date(self, target_date: date):
        """Set the date to display.
        
        Args:
            target_date: Date to show
        """
        self.current_date = target_date
        self.refresh()
    
    def refresh(self):
        """Refresh the view with current date's data."""
        # Get temperature unit from settings
        settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        temp_unit = "celsius"
        try:
            with open(settings_path) as f:
                settings = json.load(f)
                temp_unit = settings.get("display", {}).get("temperature_unit", "celsius")
        except:
            pass
        
        # Update date label with translated weekday and month
        weekday_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        weekday = t(f"week_view.{weekday_keys[self.current_date.weekday()]}")
        
        month_keys = ["january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november", "december"]
        month = t(f"year_view.{month_keys[self.current_date.month - 1]}")
        
        self.date_label.setText(f"{weekday}, {self.current_date.day}. {month} {self.current_date.year}")
        
        # Get entries for this date
        entries = self.database.get_entries_by_date(self.current_date)
        
        # Update weather
        weather = self.database.get_weather(self.current_date)
        if weather:
            temp_high = weather.get('temperature_high', '??')
            if isinstance(temp_high, (int, float)):
                temp_symbol = "°C" if temp_unit == "celsius" else "°F"
                self.weather_label.setText(
                    f"{t('weather.' + weather.get('description', 'clear').lower().replace(' ', '_'))} - "
                    f"{temp_high}{temp_symbol}"
                )
            else:
                self.weather_label.setText(t('weather.' + weather.get('description', 'clear').lower().replace(' ', '_')))
        else:
            self.weather_label.setText(t('day_view.no_events'))
        
        # Update icon slots (top 3 events)
        for i in range(3):
            container = self.icon_widgets[i]
            icon_label = container.findChild(QLabel, f"icon_{i}")
            name_label = container.findChild(QLabel, f"name_{i}")
            time_label = container.findChild(QLabel, f"time_{i}")
            
            if i < len(entries):
                entry = entries[i]
                # Use emoji as placeholder for icons
                icon_emoji = self._get_icon_emoji(entry['category'])
                icon_label.setText(icon_emoji)
                name_label.setText(entry['title'])
                
                if entry.get('start_time'):
                    time_label.setText(entry['start_time'][:5])  # HH:MM
                else:
                    time_label.setText("All day")
            else:
                icon_label.setText("🏠")
                name_label.setText("Free Time")
                time_label.setText("")
        
        # Update details section
        # Clear existing details
        while self.details_layout.count():
            child = self.details_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add entry details
        if entries:
            for entry in entries:
                detail_widget = self._create_detail_entry(entry)
                self.details_layout.addWidget(detail_widget)
        else:
            no_events_label = QLabel("No events scheduled for this day")
            no_events_label.setAlignment(Qt.AlignCenter)
            no_events_label.setStyleSheet("color: #95A5A6; font-style: italic;")
            self.details_layout.addWidget(no_events_label)
    
    def _create_detail_entry(self, entry: Dict) -> QWidget:
        """Create a detail entry widget.
        
        Args:
            entry: Entry dictionary
            
        Returns:
            Detail widget
        """
        widget = QLabel()
        widget.setStyleSheet("padding: 8px; margin: 2px; border: none;")
        widget.setWordWrap(True)
        
        time_str = entry.get('start_time', 'All day')[:5] if entry.get('start_time') else 'All day'
        text = f"• {time_str} - {entry['title']}"
        
        if entry.get('description'):
            text += f"\n  {entry['description']}"
        
        widget.setText(text)
        return widget
    
    def _get_icon_emoji(self, category: str) -> str:
        """Get emoji icon for category.
        
        Args:
            category: Category name
            
        Returns:
            Emoji string
        """
        emoji_map = {
            "School": "📚",
            "Sports": "⚽",
            "Music": "🎵",
            "Appointments": "🏥",
            "Birthday": "🎂",
            "Holiday": "🎉",
            "Vacation": "✈️",
            "Home": "🏠"
        }
        return emoji_map.get(category, "📅")
    
    def _prev_day(self):
        """Navigate to previous day."""
        self.current_date -= timedelta(days=1)
        self.refresh()
    
    def _next_day(self):
        """Navigate to next day."""
        self.current_date += timedelta(days=1)
        self.refresh()
