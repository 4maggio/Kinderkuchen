"""
Dashboard View - Main launcher screen with app tiles.

Shows tiles for:
- Calendar (weather + today's icons)
- Chromium apps (anton.app, etc.)
- Other apps (to be added)
"""

from datetime import date
from typing import Callable
import subprocess

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from utils.i18n import t


class AppTile(QFrame):
    """Single app tile widget."""
    
    clicked = pyqtSignal()
    
    def __init__(self, icon: str, title: str, subtitle: str = "", parent=None):
        """Initialize app tile.
        
        Args:
            icon: Emoji or icon string
            title: App title
            subtitle: Optional subtitle text
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setStyleSheet("""
            AppTile {
                background-color: #34495E;
                border-radius: 15px;
                padding: 20px;
            }
            AppTile:hover {
                background-color: #3E5161;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Arial", 72))
        icon_label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Subtitle (optional)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setAlignment(Qt.AlignCenter)
            subtitle_label.setFont(QFont("Arial", 12))
            subtitle_label.setStyleSheet("color: #BDC3C7;")
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class DashboardView(QWidget):
    """Dashboard view showing app launcher tiles."""
    
    calendar_clicked = pyqtSignal()
    
    def __init__(self, database, parent=None):
        """Initialize dashboard view.
        
        Args:
            database: CalendarDatabase instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.database = database
        self.current_date = date.today()
        
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header with date and today's icons
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        
        # Today's icons (3 main events)
        self.icons_layout = QHBoxLayout()
        self.icons_layout.setSpacing(20)
        self.icons_layout.setAlignment(Qt.AlignCenter)
        
        self.icon_labels = []
        for i in range(3):
            icon_label = QLabel("🏠")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFont(QFont("Arial", 64))
            icon_label.setStyleSheet("border: none; background: transparent;")
            self.icons_layout.addWidget(icon_label)
            self.icon_labels.append(icon_label)
        
        header_layout.addLayout(self.icons_layout)
        
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setFont(QFont("Arial", 16))
        self.date_label.setStyleSheet("color: #BDC3C7;")
        header_layout.addWidget(self.date_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # App tiles grid (2x2 for now, expandable)
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        
        # Calendar tile (dynamic content)
        self.calendar_tile = self._create_calendar_tile()
        self.grid.addWidget(self.calendar_tile, 0, 0)
        
        # Anton.app tile
        anton_tile = AppTile("🎓", "Anton.app", "Lernen & Üben")
        anton_tile.clicked.connect(self._launch_anton)
        self.grid.addWidget(anton_tile, 0, 1)
        
        # OS tile (boot to LXDE desktop)
        os_tile = AppTile("🖥️", "Desktop", "LXDE starten")
        os_tile.clicked.connect(self._launch_lxde)
        self.grid.addWidget(os_tile, 1, 0)
        
        placeholder2 = AppTile("📚", "Bücher", "Bald verfügbar")
        placeholder2.setEnabled(False)
        placeholder2.setStyleSheet("""
            AppTile {
                background-color: #2C3E50;
                border: 2px dashed #34495E;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        self.grid.addWidget(placeholder2, 1, 1)
        
        layout.addLayout(self.grid, 1)
    
    def _create_calendar_tile(self) -> AppTile:
        """Create calendar tile with dynamic content.
        
        Returns:
            Calendar app tile
        """
        tile = AppTile("📅", "Kalender", "Heute")
        tile.clicked.connect(self.calendar_clicked.emit)
        
        # Store reference to update content
        self.calendar_tile_widget = tile
        
        return tile
    
    def refresh(self):
        """Refresh dashboard content."""
        # Update date
        weekday_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        weekday = t(f"week_view.{weekday_keys[self.current_date.weekday()]}")
        
        month_keys = ["january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november", "december"]
        month = t(f"year_view.{month_keys[self.current_date.month - 1]}")
        
        self.date_label.setText(f"{weekday}, {self.current_date.day}. {month} {self.current_date.year}")
        
        # Update today's icons
        self._update_today_icons()
        
        # Update calendar tile with today's info
        self._update_calendar_tile()
    
    def _update_today_icons(self):
        """Update today's icon display with main events."""
        entries = self.database.get_entries_by_date(self.current_date)
        
        # Show top 3 events
        for i in range(3):
            if i < len(entries):
                entry = entries[i]
                icon_emoji = self._get_icon_emoji(entry['category'])
                self.icon_labels[i].setText(icon_emoji)
            else:
                self.icon_labels[i].setText("🏠")  # Default home icon
    
    def _update_calendar_tile(self):
        """Update calendar tile with today's weather and events."""
        # Get today's entries
        entries = self.database.get_entries_by_date(self.current_date)
        weather = self.database.get_weather(self.current_date)
        
        # Build subtitle with weather and event count
        subtitle_parts = []
        
        if weather:
            weather_icon = self._get_weather_emoji(weather.get('description', 'clear'))
            subtitle_parts.append(weather_icon)
        
        if entries:
            event_count = len(entries)
            subtitle_parts.append(f"{event_count} Termine")
        else:
            subtitle_parts.append("Keine Termine")
        
        # Update tile (need to recreate due to AppTile design)
        # For now, keep simple - will show static "Heute"
        # TODO: Make AppTile content dynamic
    
    def _get_weather_emoji(self, description: str) -> str:
        """Get weather emoji for description.
        
        Args:
            description: Weather description
            
        Returns:
            Weather emoji
        """
        desc_lower = description.lower()
        
        if 'clear' in desc_lower or 'sunny' in desc_lower:
            return '☀️'
        elif 'partly' in desc_lower or 'partial' in desc_lower:
            return '⛅'
        elif 'cloud' in desc_lower:
            return '☁️'
        elif 'rain' in desc_lower or 'drizzle' in desc_lower:
            return '🌧'
        elif 'thunder' in desc_lower or 'storm' in desc_lower:
            return '⛈'
        elif 'snow' in desc_lower:
            return '❄️'
        elif 'fog' in desc_lower or 'mist' in desc_lower:
            return '🌫'
        else:
            return '☀️'
    
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
    
    def _launch_anton(self):
        """Launch Anton.app in Chromium kiosk mode."""
        try:
            # Launch Chromium in kiosk mode
            subprocess.Popen([
                "chromium-browser",
                "--kiosk",
                "--noerrdialogs",
                "--disable-infobars",
                "--no-first-run",
                "--fast",
                "--fast-start",
                "--disable-features=TranslateUI",
                "--disk-cache-dir=/dev/null",
                "https://anton.app"
            ])
        except FileNotFoundError:
            # Try alternative Chromium command (Windows)
            try:
                subprocess.Popen([
                    "chrome",
                    "--kiosk",
                    "--noerrdialogs",
                    "--disable-infobars",
                    "https://anton.app"
                ])
            except Exception as e:
                print(f"Error launching Chromium: {e}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Fehler",
                    f"Chromium konnte nicht gestartet werden.\n\nFehler: {e}"
                )
    
    def _launch_lxde(self):
        """Boot to LXDE desktop environment."""
        try:
            # Kill this app and start LXDE
            # This requires the launcher script to handle the restart
            print("Requesting LXDE desktop boot...")
            
            # Write flag file for launcher to detect
            import os
            flag_file = "/tmp/kidlauncher_start_lxde"
            with open(flag_file, 'w') as f:
                f.write("1")
            
            # Exit app - launcher script will detect flag and start LXDE
            from PyQt5.QtWidgets import QApplication
            QApplication.instance().quit()
            
        except Exception as e:
            print(f"Error requesting LXDE boot: {e}")
