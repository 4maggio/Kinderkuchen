"""Navigation bar widget for view switching and app control."""

from typing import Optional

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from utils.i18n import t
from themes.theme_manager import Theme, ThemeColors


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
        self.theme_colors = ThemeColors()
        self.scale_factor = 1.0
        self._init_ui()
        self._apply_theme_styles()
    
    def _init_ui(self):
        """Initialize the UI."""
        self.setFixedHeight(60)
        self.setObjectName("NavigationBar")
        
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
        self.rotate_btn = QPushButton("🔄")
        self.rotate_btn.setFixedSize(50, 50)
        self.rotate_btn.setToolTip("Display rotieren")
        self.rotate_btn.clicked.connect(self.rotation_clicked.emit)
        layout.addWidget(self.rotate_btn)
        
        # Settings button (will show timer when screentime active)
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(50, 50)
        self.settings_btn.setToolTip("Parental Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)
        
        # Store for timer display
        self.showing_timer = False

    def _apply_theme_styles(self):
        """Apply stylesheet derived from the current theme colors."""
        c = self.theme_colors
        font_size = max(12, int(14 * self.scale_factor))
        padding_v = max(4, int(8 * self.scale_factor))
        padding_h = max(8, int(16 * self.scale_factor))
        min_width = max(60, int(80 * self.scale_factor))
        self.setStyleSheet(f"""
            QWidget#NavigationBar {{
                background-color: {c.background_secondary};
            }}
            QWidget#NavigationBar QPushButton {{
                background-color: {c.background_secondary};
                color: {c.text_secondary};
                border: none;
                border-radius: 8px;
                padding: {padding_v}px {padding_h}px;
                font-size: {font_size}px;
                font-weight: bold;
                min-width: {min_width}px;
            }}
            QWidget#NavigationBar QPushButton:hover {{
                background-color: {c.background_hover};
            }}
            QWidget#NavigationBar QPushButton[active="true"] {{
                background-color: {c.accent};
                color: {c.text_primary};
            }}
        """)

    def set_scale_factor(self, scale_factor: float):
        """Resize navigation controls for smaller displays."""
        self.scale_factor = max(0.6, min(scale_factor, 1.0))
        self.setFixedHeight(int(60 * self.scale_factor))
        side_size = int(50 * self.scale_factor)
        if hasattr(self, 'rotate_btn'):
            self.rotate_btn.setFixedSize(side_size, side_size)
        if hasattr(self, 'settings_btn'):
            settings_width = int((100 if self.showing_timer else 50) * self.scale_factor)
            self.settings_btn.setFixedSize(settings_width, side_size)
        base_view_font = max(12, int(14 * self.scale_factor))
        for button in getattr(self, 'view_buttons', {}).values():
            font = button.font()
            font.setPointSize(base_view_font)
            button.setFont(font)
        self._apply_theme_styles()

    def apply_theme(self, theme: Optional[Theme]):
        """Update the navigation bar palette based on theme colors."""
        self.theme_colors = theme.colors if theme else ThemeColors()
        self._apply_theme_styles()
    
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
        self.settings_btn.setFixedWidth(int(100 * self.scale_factor))
        self.settings_btn.setToolTip("Screen Time Management")
        self.showing_timer = True
    
    def reset_settings_display(self):
        """Reset settings button to show gear icon."""
        self.settings_btn.setText("⚙")
        self.settings_btn.setFixedWidth(int(50 * self.scale_factor))
        self.settings_btn.setToolTip("Parental Settings")
        self.showing_timer = False
