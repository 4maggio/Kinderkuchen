"""
Week View - Seven-column layout showing the week at a glance.

Shows Monday-Sunday with weather and activity icons for each day.
"""

from datetime import date, timedelta
from typing import List, Dict

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGridLayout, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont

from utils.i18n import t


class WeekView(QWidget):
    """Week view widget showing 7-day overview."""
    
    day_clicked = pyqtSignal(date)  # Emits date when a day is clicked
    
    def __init__(self, database, current_date: date = None):
        """Initialize week view.
        
        Args:
            database: CalendarDatabase instance
            current_date: Initial date (will show week containing this date)
        """
        super().__init__()
        
        self.database = database
        self.current_date = current_date or date.today()
        self.week_start = self._get_week_start(self.current_date)
        
        self._init_ui()
        self.refresh()
    
    def _init_ui(self):
        """Initialize the user interface."""
        self.setStyleSheet("""
            QWidget {
                background-color: #2C3E50;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #34495E;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #1ABC9C;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Week header with navigation
        header_layout = QHBoxLayout()
        
        self.prev_week_btn = QPushButton("◀ " + t('week_view.previous_week'))
        self.prev_week_btn.clicked.connect(self._prev_week)
        header_layout.addWidget(self.prev_week_btn)
        
        self.week_label = QLabel()
        self.week_label.setAlignment(Qt.AlignCenter)
        self.week_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(self.week_label, 1)
        
        self.next_week_btn = QPushButton(t('week_view.next_week') + " ▶")
        self.next_week_btn.clicked.connect(self._next_week)
        header_layout.addWidget(self.next_week_btn)
        
        layout.addLayout(header_layout)
        
        # Grid for 7 days
        grid = QGridLayout()
        grid.setSpacing(5)
        
        self.day_widgets = []
        
        for col in range(7):
            day_widget = self._create_day_column(col)
            grid.addWidget(day_widget, 0, col)
            self.day_widgets.append(day_widget)
        
        layout.addLayout(grid, 1)
    
    def _create_day_column(self, col_index: int) -> QWidget:
        """Create a day column widget.
        
        Args:
            col_index: Column index (0=Monday, 6=Sunday)
            
        Returns:
            Day column widget
        """
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #34495E;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        container.setObjectName(f"day_{col_index}")
        
        # Make clickable
        container.mousePressEvent = lambda event, idx=col_index: self._on_day_clicked(idx)
        container.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(5)
        
        # Day name
        day_label = QLabel()
        day_label.setAlignment(Qt.AlignCenter)
        day_label.setFont(QFont("Arial", 12, QFont.Bold))
        day_label.setStyleSheet("border: none;")
        day_label.setObjectName(f"day_name_{col_index}")
        layout.addWidget(day_label)
        
        # Date number
        date_label = QLabel()
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setFont(QFont("Arial", 10))
        date_label.setStyleSheet("border: none;")
        date_label.setObjectName(f"date_num_{col_index}")
        layout.addWidget(date_label)
        
        # Weather icon
        weather_label = QLabel()
        weather_label.setAlignment(Qt.AlignCenter)
        weather_label.setFont(QFont("Arial", 24))
        weather_label.setStyleSheet("border: none;")
        weather_label.setObjectName(f"weather_{col_index}")
        layout.addWidget(weather_label)
        
        # Activity icons (3 slots)
        for i in range(3):
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFont(QFont("Arial", 32))
            icon_label.setStyleSheet("border: none; padding: 2px;")
            icon_label.setObjectName(f"icon_{col_index}_{i}")
            layout.addWidget(icon_label)
        
        layout.addStretch()
        
        return container
    
    def _get_week_start(self, target_date: date) -> date:
        """Get the Monday of the week containing target_date.
        
        Args:
            target_date: Reference date
            
        Returns:
            Date of Monday
        """
        # weekday(): Monday=0, Sunday=6
        days_since_monday = target_date.weekday()
        monday = target_date - timedelta(days=days_since_monday)
        return monday
    
    def refresh(self):
        """Refresh the view with current week's data."""
        # Update week label with translation
        week_end = self.week_start + timedelta(days=6)
        
        # Translate month names
        month_keys = ["january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november", "december"]
        start_month = t(f"year_view.{month_keys[self.week_start.month - 1]}")
        end_month = t(f"year_view.{month_keys[week_end.month - 1]}")
        
        self.week_label.setText(
            f"{t('week_view.week_of')} {self.week_start.day}. {start_month} - {week_end.day}. {end_month} {week_end.year}"
        )
        
        # Update each day column
        for col in range(7):
            current_day = self.week_start + timedelta(days=col)
            self._update_day_column(col, current_day)
    
    def _update_day_column(self, col: int, day_date: date):
        """Update a day column with data.
        
        Args:
            col: Column index
            day_date: Date for this column
        """
        container = self.day_widgets[col]
        
        # Highlight today
        is_today = day_date == date.today()
        if is_today:
            container.setStyleSheet("""
                QFrame {
                    background-color: #1ABC9C;
                    border-radius: 8px;
                    padding: 5px;
                    border: 2px solid #16A085;
                }
            """)
        else:
            container.setStyleSheet("""
                QFrame {
                    background-color: #34495E;
                    border-radius: 8px;
                    padding: 5px;
                }
            """)
        
        # Update day name with translation
        day_name_label = container.findChild(QLabel, f"day_name_{col}")
        weekday_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        day_name_label.setText(t(f"week_view.{weekday_keys[day_date.weekday()]}"))
        
        # Update date number
        date_num_label = container.findChild(QLabel, f"date_num_{col}")
        date_num_label.setText(day_date.strftime("%d"))  # 07, 08, etc.
        
        # Update weather
        weather_label = container.findChild(QLabel, f"weather_{col}")
        weather = self.database.get_weather(day_date)
        if weather:
            weather_emoji = self._get_weather_emoji(weather.get('description', ''))
            weather_label.setText(weather_emoji)
        else:
            weather_label.setText("☀")
        
        # Get entries for this day
        entries = self.database.get_entries_by_date(day_date)
        
        # Update activity icons (top 3)
        for i in range(3):
            icon_label = container.findChild(QLabel, f"icon_{col}_{i}")
            
            if i < len(entries):
                entry = entries[i]
                emoji = self._get_icon_emoji(entry['category'])
                icon_label.setText(emoji)
            else:
                icon_label.setText("")
    
    def _get_weather_emoji(self, description: str) -> str:
        """Get weather emoji from description.
        
        Args:
            description: Weather description
            
        Returns:
            Weather emoji
        """
        description_lower = description.lower()
        
        # Map weather descriptions to icons
        if 'clear' in description_lower or 'sunny' in description_lower:
            return "☀"  # sunny
        elif 'partly' in description_lower and 'cloud' in description_lower:
            return "⛅"  # partly_cloudy
        elif 'cloud' in description_lower:
            return "☁"  # cloudy
        elif 'rain' in description_lower or 'drizzle' in description_lower:
            return "🌧"  # rainy
        elif 'storm' in description_lower or 'thunder' in description_lower:
            return "⛈"  # stormy
        elif 'snow' in description_lower:
            return "❄"  # snowy
        elif 'fog' in description_lower or 'mist' in description_lower:
            return "🌫"  # foggy
        else:
            return "☀"
    
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
    
    def _on_day_clicked(self, col_index: int):
        """Handle day column click.
        
        Args:
            col_index: Index of clicked column
        """
        clicked_date = self.week_start + timedelta(days=col_index)
        self.day_clicked.emit(clicked_date)
    
    def _prev_week(self):
        """Navigate to previous week."""
        self.week_start -= timedelta(days=7)
        self.refresh()
    
    def _next_week(self):
        """Navigate to next week."""
        self.week_start += timedelta(days=7)
        self.refresh()
