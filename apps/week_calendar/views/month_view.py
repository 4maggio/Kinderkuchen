"""
Month View - Traditional calendar grid view.

Shows a month in grid layout with mini-icons for events.
"""

from datetime import date, timedelta
import calendar

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from utils.i18n import t


class MonthView(QWidget):
    """Month view widget showing calendar grid."""
    
    day_clicked = pyqtSignal(date)  # Emits date when a day is clicked
    
    def __init__(self, database, current_date: date = None):
        """Initialize month view.
        
        Args:
            database: CalendarDatabase instance
            current_date: Initial date (will show this month)
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
        
        # Month header with navigation
        header_layout = QHBoxLayout()
        
        self.prev_month_btn = QPushButton("◀ " + t('month_view.previous_month'))
        self.prev_month_btn.clicked.connect(self._prev_month)
        header_layout.addWidget(self.prev_month_btn)
        
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        self.month_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(self.month_label, 1)
        
        self.next_month_btn = QPushButton(t('month_view.next_month') + " ▶")
        self.next_month_btn.clicked.connect(self._next_month)
        header_layout.addWidget(self.next_month_btn)
        
        layout.addLayout(header_layout)
        
        # Day names header with translations
        day_names_layout = QHBoxLayout()
        day_names_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for day_key in day_names_keys:
            label = QLabel(t(f"week_view.{day_key}"))
            label.setAlignment(Qt.AlignCenter)
            label.setFont(QFont("Arial", 10, QFont.Bold))
            day_names_layout.addWidget(label)
        
        layout.addLayout(day_names_layout)
        
        # Calendar grid (6 rows x 7 columns max)
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(3)
        
        self.day_cells = []
        
        for row in range(6):
            for col in range(7):
                cell = self._create_day_cell(row, col)
                self.calendar_grid.addWidget(cell, row, col)
                self.day_cells.append(cell)
        
        layout.addLayout(self.calendar_grid, 1)
    
    def _create_day_cell(self, row: int, col: int) -> QWidget:
        """Create a day cell widget.
        
        Args:
            row: Row index
            col: Column index
            
        Returns:
            Day cell widget
        """
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #34495E;
                border-radius: 5px;
                padding: 3px;
            }
        """)
        container.setFixedHeight(60)
        container.setCursor(Qt.PointingHandCursor)
        container.setObjectName(f"cell_{row}_{col}")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignTop)
        
        # Day number
        day_label = QLabel()
        day_label.setAlignment(Qt.AlignCenter)
        day_label.setFont(QFont("Arial", 12, QFont.Bold))
        day_label.setObjectName(f"day_num_{row}_{col}")
        layout.addWidget(day_label)
        
        # Icons container
        icons_label = QLabel()
        icons_label.setAlignment(Qt.AlignCenter)
        icons_label.setFont(QFont("Arial", 16))
        icons_label.setObjectName(f"icons_{row}_{col}")
        layout.addWidget(icons_label)
        
        return container
    
    def set_date(self, target_date: date):
        """Set the date (month) to display.
        
        Args:
            target_date: Date in the month to show
        """
        self.current_date = target_date
        self.refresh()
    
    def refresh(self):
        """Refresh the view with current month's data."""
        year = self.current_date.year
        month = self.current_date.month
        
        # Update month label with translation
        month_keys = ["january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november", "december"]
        month_name = t(f"year_view.{month_keys[month - 1]}")
        self.month_label.setText(f"{month_name} {year}")
        
        # Get calendar data
        cal = calendar.monthcalendar(year, month)
        
        # Flatten and pad calendar to 42 cells (6 rows x 7 days)
        all_days = []
        for week in cal:
            all_days.extend(week)
        
        # Pad to 42 cells
        while len(all_days) < 42:
            all_days.append(0)
        
        # Update each cell
        for idx, day_num in enumerate(all_days):
            row = idx // 7
            col = idx % 7
            
            if day_num == 0:
                self._update_cell(row, col, None)
            else:
                cell_date = date(year, month, day_num)
                self._update_cell(row, col, cell_date)
    
    def _update_cell(self, row: int, col: int, cell_date: date = None):
        """Update a calendar cell.
        
        Args:
            row: Row index
            col: Column index
            cell_date: Date for this cell (None for empty cells)
        """
        container = self.findChild(QFrame, f"cell_{row}_{col}")
        day_label = container.findChild(QLabel, f"day_num_{row}_{col}")
        icons_label = container.findChild(QLabel, f"icons_{row}_{col}")
        
        if cell_date is None:
            # Empty cell
            day_label.setText("")
            icons_label.setText("")
            container.setStyleSheet("""
                QFrame {
                    background-color: #2C3E50;
                    border-radius: 5px;
                    padding: 3px;
                }
            """)
            container.mousePressEvent = lambda event: None
            return
        
        # Update day number
        day_label.setText(str(cell_date.day))
        
        # Highlight today
        is_today = cell_date == date.today()
        if is_today:
            container.setStyleSheet("""
                QFrame {
                    background-color: #1ABC9C;
                    border-radius: 5px;
                    padding: 3px;
                    border: 2px solid #16A085;
                }
            """)
        else:
            container.setStyleSheet("""
                QFrame {
                    background-color: #34495E;
                    border-radius: 5px;
                    padding: 3px;
                }
            """)
        
        # Get entries for this date
        entries = self.database.get_entries_by_date(cell_date)
        
        # Show mini icons (up to 3)
        icons_text = ""
        for i, entry in enumerate(entries[:3]):
            if i > 0:
                icons_text += " "
            icons_text += self._get_mini_emoji(entry['category'])
        
        icons_label.setText(icons_text)
        
        # Set click handler
        container.mousePressEvent = lambda event, d=cell_date: self._on_cell_clicked(d)
    
    def _get_mini_emoji(self, category: str) -> str:
        """Get smaller emoji for category.
        
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
    
    def _on_cell_clicked(self, cell_date: date):
        """Handle cell click.
        
        Args:
            cell_date: Date of clicked cell
        """
        self.day_clicked.emit(cell_date)
    
    def _prev_month(self):
        """Navigate to previous month."""
        # Go to first day of current month, then subtract 1 day
        first_of_month = self.current_date.replace(day=1)
        self.current_date = first_of_month - timedelta(days=1)
        self.refresh()
    
    def _next_month(self):
        """Navigate to next month."""
        # Go to first day of next month
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1, day=1)
        self.refresh()
