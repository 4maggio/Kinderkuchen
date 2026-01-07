"""
Navigation bar widget for view switching and app control.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from utils.i18n import t


class NavigationBar(QWidget):
    """Top navigation bar with view tabs and back button."""
    
    view_changed = pyqtSignal(str)  # Emits view name
    back_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()  # Emits when settings button is clicked
    rotation_clicked = pyqtSignal()  # Emits when rotation button is clicked
    
    def __init__(self, parent=None):
        """Initialize navigation bar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.active_view = "week"
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QWidget {
                background-color: #34495E;
            }
            QPushButton {
                background-color: #34495E;
                color: #BDC3C7;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3E5161;
            }
            QPushButton[active="true"] {
                background-color: #1ABC9C;
                color: white;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Back button (left side)
        self.back_btn = QPushButton(t('navigation.back'))
        self.back_btn.clicked.connect(self.back_clicked.emit)
        self.back_btn.setFixedWidth(100)
        layout.addWidget(self.back_btn)
        
        # Spacer
        layout.addSpacing(20)
        
        # View buttons
        self.day_btn = QPushButton(t('navigation.day'))
        self.day_btn.clicked.connect(lambda: self._on_view_clicked("day"))
        layout.addWidget(self.day_btn)
        
        self.week_btn = QPushButton(t('navigation.week'))
        self.week_btn.clicked.connect(lambda: self._on_view_clicked("week"))
        layout.addWidget(self.week_btn)
        
        self.month_btn = QPushButton(t('navigation.month'))
        self.month_btn.clicked.connect(lambda: self._on_view_clicked("month"))
        layout.addWidget(self.month_btn)
        
        self.year_btn = QPushButton(t('navigation.year'))
        self.year_btn.clicked.connect(lambda: self._on_view_clicked("year"))
        layout.addWidget(self.year_btn)
        
        # Store buttons for easy access
        self.view_buttons = {
            "day": self.day_btn,
            "week": self.week_btn,
            "month": self.month_btn,
            "year": self.year_btn
        }
        
        # Spacer to push everything to the left
        layout.addStretch()
        
        # Rotation button
        rotate_btn = QPushButton("🔄")
        rotate_btn.setFixedSize(50, 50)
        rotate_btn.setToolTip("Display rotieren")
        rotate_btn.clicked.connect(self.rotation_clicked.emit)
        layout.addWidget(rotate_btn)
        
        # Settings button (will show timer when screentime active)
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(50, 50)
        self.settings_btn.setToolTip("Parental Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)
        
        # Store for timer display
        self.showing_timer = False
    
    def _on_view_clicked(self, view_name: str):
        """Handle view button click.
        
        Args:
            view_name: Name of clicked view
        """
        self.set_active_view(view_name)
        self.view_changed.emit(view_name)
    
    def set_active_view(self, view_name: str):
        """Set the active view and update button styles.
        
        Args:
            view_name: Name of active view (None for dashboard)
        """
        self.active_view = view_name
        
        # Show/hide view buttons based on mode
        is_dashboard = (view_name is None)
        for name, button in self.view_buttons.items():
            button.setVisible(not is_dashboard)
        
        # Update button properties to trigger style update
        if not is_dashboard:
            for name, button in self.view_buttons.items():
                is_active = (view_name == name)
                button.setProperty("active", "true" if is_active else "false")
                # Force style refresh
                button.style().unpolish(button)
                button.style().polish(button)
    
    def update_screentime_display(self, remaining_seconds: int):
        """Update settings button to show remaining screen time.
        
        Args:
            remaining_seconds: Remaining seconds of screen time
        """
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        self.settings_btn.setText(f"⏱{minutes:02d}:{seconds:02d}")
        self.settings_btn.setFixedWidth(100)
        self.settings_btn.setToolTip("Screen Time Management")
        self.showing_timer = True
    
    def reset_settings_display(self):
        """Reset settings button to show gear icon."""
        self.settings_btn.setText("⚙")
        self.settings_btn.setFixedWidth(50)
        self.settings_btn.setToolTip("Parental Settings")
        self.showing_timer = False
