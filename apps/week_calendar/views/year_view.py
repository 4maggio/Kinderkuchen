"""
Year View - 4x3 grid showing all 12 months with special events only.

Shows birthdays, holidays, and vacations in a year overview.
"""

from datetime import date
from typing import List, Dict

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from utils.i18n import t


class YearView(QWidget):
    """Year view widget showing 12-month overview with special events."""
    
    month_clicked = pyqtSignal(int, int)  # Emits (year, month) when clicked
    
    def __init__(self, database, current_date: date = None):
        """Initialize year view.
        
        Args:
            database: CalendarDatabase instance
            current_date: Initial date (will show this year)
        """
        super().__init__()
        
        self.database = database
        self.current_date = current_date or date.today()
        
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
        
        # Year header with navigation
        header_layout = QHBoxLayout()
        
        self.prev_year_btn = QPushButton("◀ " + t('year_view.previous_year'))
        self.prev_year_btn.clicked.connect(self._prev_year)
        header_layout.addWidget(self.prev_year_btn)
        
        self.year_label = QLabel()
        self.year_label.setAlignment(Qt.AlignCenter)
        self.year_label.setFont(QFont("Arial", 20, QFont.Bold))
        header_layout.addWidget(self.year_label, 1)
        
        self.next_year_btn = QPushButton(t('year_view.next_year') + " ▶")
        self.next_year_btn.clicked.connect(self._next_year)
        header_layout.addWidget(self.next_year_btn)
        
        layout.addLayout(header_layout)
        
        # 4x3 grid for 12 months with translated names
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        
        self.month_widgets = []
        
        # Create all 12 month widgets (will be positioned dynamically)
        self.month_keys = [
            "january", "february", "march", "april",
            "may", "june", "july", "august",
            "september", "october", "november", "december"
        ]
        
        for i in range(12):
            month_name = t(f"year_view.{self.month_keys[i]}")
            month_widget = self._create_month_box(i + 1, month_name)
            self.month_widgets.append(month_widget)
        
        layout.addLayout(self.grid, 1)
    
    def _create_month_box(self, month_num: int, month_name: str) -> QWidget:
        """Create a month box widget.
        
        Args:
            month_num: Month number (1-12)
            month_name: Month name
            
        Returns:
            Month box widget
        """
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #34495E;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        container.setCursor(Qt.PointingHandCursor)
        container.setObjectName(f"month_{month_num}")
        container.mousePressEvent = lambda event, m=month_num: self._on_month_clicked(m)
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(5)
        
        # Month name
        name_label = QLabel(month_name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(name_label)
        
        # Special events area
        events_label = QLabel()
        events_label.setAlignment(Qt.AlignCenter)
        events_label.setFont(QFont("Arial", 24))
        events_label.setWordWrap(True)
        events_label.setObjectName(f"events_{month_num}")
        layout.addWidget(events_label)
        
        # Event count label
        count_label = QLabel()
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setFont(QFont("Arial", 9))
        count_label.setStyleSheet("color: #95A5A6;")
        count_label.setObjectName(f"count_{month_num}")
        layout.addWidget(count_label)
        
        return container
    
    def refresh(self):
        """Refresh the view with current year's data."""
        import json
        from pathlib import Path
        
        year = self.current_date.year
        
        # Update year label
        self.year_label.setText(str(year))
        
        # Load start month setting
        settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        start_month = 1  # Default to January
        try:
            with open(settings_path) as f:
                settings = json.load(f)
                mode = settings.get("year_view", {}).get("start_month_mode", "current")
                if mode == "custom":
                    start_month = settings.get("year_view", {}).get("custom_start_month", 1)
                elif mode == "january":
                    start_month = 1
                elif mode == "current":
                    start_month = date.today().month
        except:
            pass
        
        # Clear grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Re-add month widgets in custom order
        for i in range(12):
            month_num = ((start_month - 1 + i) % 12) + 1
            row = i // 3
            col = i % 3
            
            # Find the widget for this month
            month_widget = self.month_widgets[month_num - 1]
            self.grid.addWidget(month_widget, row, col)
            
            # Update month box data
            self._update_month_box(month_num, year)
    
    def _update_month_box(self, month_num: int, year: int):
        """Update a month box with special events.
        
        Args:
            month_num: Month number (1-12)
            year: Year
        """
        container = self.findChild(QFrame, f"month_{month_num}")
        events_label = container.findChild(QLabel, f"events_{month_num}")
        count_label = container.findChild(QLabel, f"count_{month_num}")
        
        # Highlight current month
        is_current_month = (month_num == date.today().month and year == date.today().year)
        if is_current_month:
            container.setStyleSheet("""
                QFrame {
                    background-color: #1ABC9C;
                    border-radius: 8px;
                    padding: 8px;
                    border: 2px solid #16A085;
                }
            """)
        else:
            container.setStyleSheet("""
                QFrame {
                    background-color: #34495E;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
        
        # Get special events for this month
        special_events = self.database.get_special_events_by_month(year, month_num)
        
        if special_events:
            # Show up to 4 event icons
            icons_text = ""
            for i, event in enumerate(special_events[:4]):
                if i > 0 and i % 2 == 0:
                    icons_text += "\n"
                elif i > 0:
                    icons_text += " "
                icons_text += self._get_special_emoji(event['category'])
            
            if len(special_events) > 4:
                icons_text += "\n..."
            
            events_label.setText(icons_text)
            
            # Event count
            count_text = f"{len(special_events)} event"
            if len(special_events) > 1:
                count_text += "s"
            count_label.setText(count_text)
        else:
            events_label.setText("—")
            count_label.setText("No events")
    
    def _get_special_emoji(self, category: str) -> str:
        """Get emoji for special event category.
        
        Args:
            category: Category name
            
        Returns:
            Emoji string
        """
        emoji_map = {
            "Birthday": "🎂",
            "Holiday": "🎉",
            "Vacation": "✈️"
        }
        return emoji_map.get(category, "⭐")
    
    def _on_month_clicked(self, month_num: int):
        """Handle month box click.
        
        Args:
            month_num: Month number that was clicked
        """
        year = self.current_date.year
        self.month_clicked.emit(year, month_num)
    
    def _prev_year(self):
        """Navigate to previous year."""
        self.current_date = self.current_date.replace(year=self.current_date.year - 1)
        self.refresh()
    
    def _next_year(self):
        """Navigate to next year."""
        self.current_date = self.current_date.replace(year=self.current_date.year + 1)
        self.refresh()
