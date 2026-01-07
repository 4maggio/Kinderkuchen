"""
Screen Time Manager - Manages screen time limits and reminders.

Features:
- Configurable screen time limit
- Multiple reminder notifications
- Full-screen analog clock display
- PIN-protected unlock after time expires
"""

from datetime import datetime, timedelta, date
from typing import List, Optional, Callable
import json
from pathlib import Path

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QDialog, QLineEdit, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QPolygon

from utils.i18n import t
from utils.screentime_manager import ScreenTimeController


class AnalogClockWidget(QWidget):
    """Analog clock showing remaining time."""
    
    def __init__(self, remaining_seconds: int = 0, parent=None):
        """Initialize analog clock.
        
        Args:
            remaining_seconds: Remaining time in seconds (default: 0)
            parent: Parent widget
        """
        super().__init__(parent)
        self.remaining_seconds = remaining_seconds
        self.total_seconds = remaining_seconds if remaining_seconds > 0 else 3600
        self.setMinimumSize(300, 300)
    
    def set_remaining(self, seconds: int, total_seconds: int = None):
        """Update remaining time.
        
        Args:
            seconds: Remaining seconds
            total_seconds: Total seconds (optional)
        """
        self.remaining_seconds = seconds
        if total_seconds is not None:
            self.total_seconds = total_seconds
        self.update()
    
    def paintEvent(self, event):
        """Paint the analog clock."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        size = min(width, height)
        
        # Calculate center and radius
        center_x = width // 2
        center_y = height // 2
        radius = size // 2 - 20
        
        # Draw clock circle
        painter.setPen(QPen(QColor(52, 73, 94), 3))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw filled arc showing remaining time
        progress = (self.remaining_seconds / self.total_seconds) if self.total_seconds > 0 else 0
        span_angle = int(360 * 16 * progress)  # Qt uses 16ths of a degree
        
        painter.setBrush(QColor(26, 188, 156, 100))
        painter.setPen(Qt.NoPen)
        painter.drawPie(center_x - radius, center_y - radius, radius * 2, radius * 2, 90 * 16, -span_angle)
        
        # Draw hour markers
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        for i in range(12):
            angle = i * 30  # 30 degrees per hour
            outer_x = center_x + int(radius * 0.9 * self._cos(angle))
            outer_y = center_y - int(radius * 0.9 * self._sin(angle))
            inner_x = center_x + int(radius * 0.8 * self._cos(angle))
            inner_y = center_y - int(radius * 0.8 * self._sin(angle))
            painter.drawLine(inner_x, inner_y, outer_x, outer_y)
        
        # Draw hand showing remaining time
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        
        # Minute hand
        minute_angle = (minutes % 60) * 6  # 6 degrees per minute
        hand_length = radius * 0.7
        hand_x = center_x + int(hand_length * self._cos(minute_angle - 90))
        hand_y = center_y - int(hand_length * self._sin(minute_angle - 90))
        painter.setPen(QPen(QColor(231, 76, 60), 4))
        painter.drawLine(center_x, center_y, hand_x, hand_y)
        
        # Center dot
        painter.setBrush(QColor(231, 76, 60))
        painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)
        
        # Draw time text
        minutes_left = self.remaining_seconds // 60
        seconds_left = self.remaining_seconds % 60
        time_text = f"{minutes_left:02d}:{seconds_left:02d}"
        
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 24, QFont.Bold))
        text_rect = QRect(0, center_y + radius - 50, width, 40)
        painter.drawText(text_rect, Qt.AlignCenter, time_text)
    
    def _cos(self, angle_degrees: float) -> float:
        """Calculate cosine (angle in degrees)."""
        import math
        return math.cos(math.radians(angle_degrees))
    
    def _sin(self, angle_degrees: float) -> float:
        """Calculate sine (angle in degrees)."""
        import math
        return math.sin(math.radians(angle_degrees))


class ReminderDialog(QDialog):
    """Full-screen reminder dialog with analog clock."""
    
    def __init__(self, remaining_minutes: int, total_minutes: int, parent=None):
        """Initialize reminder dialog.
        
        Args:
            remaining_minutes: Minutes remaining
            total_minutes: Total screen time minutes
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle(t('screentime.reminder_title'))
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Set to fullscreen
        if parent:
            self.setGeometry(parent.geometry())
        
        self._init_ui(remaining_minutes, total_minutes)
    
    def _init_ui(self, remaining_minutes: int, total_minutes: int):
        """Initialize UI."""
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(44, 62, 80, 250);
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #1ABC9C;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 20px 40px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #16A085;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)
        
        # Title
        title = QLabel(t('screentime.reminder_title'))
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Message
        message = QLabel(t('screentime.reminder_message', minutes=remaining_minutes))
        message.setFont(QFont("Arial", 18))
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # Analog clock
        self.clock = AnalogClockWidget(remaining_minutes * 60)
        self.clock.setFixedSize(400, 400)
        layout.addWidget(self.clock, 0, Qt.AlignCenter)
        
        # OK button
        ok_btn = QPushButton(t('common.ok'))
        ok_btn.setFixedWidth(200)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, 0, Qt.AlignCenter)


class LockDialog(QDialog):
    """Full-screen lock dialog requiring PIN to unlock."""
    
    def __init__(self, pin_code: str, parent=None):
        """Initialize lock dialog.
        
        Args:
            pin_code: Correct PIN code
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.pin_code = pin_code
        self.setWindowTitle(t('screentime.locked_title'))
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Set to fullscreen
        if parent:
            self.setGeometry(parent.geometry())
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(231, 76, 60, 250);
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: white;
                color: black;
                border: none;
                border-radius: 10px;
                padding: 15px;
                font-size: 24px;
            }
            QPushButton {
                background-color: #C0392B;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #922B21;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)
        
        # Lock icon
        lock_label = QLabel("🔒")
        lock_label.setFont(QFont("Arial", 120))
        lock_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(lock_label)
        
        # Title
        title = QLabel(t('screentime.locked_title'))
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Message
        message = QLabel(t('screentime.locked_message'))
        message.setFont(QFont("Arial", 18))
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # PIN input
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setMaxLength(6)
        self.pin_input.setPlaceholderText(t('settings.security_tab.pin_placeholder'))
        self.pin_input.setFixedWidth(300)
        self.pin_input.returnPressed.connect(self._check_pin)
        layout.addWidget(self.pin_input, 0, Qt.AlignCenter)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #FFEB3B; font-weight: bold;")
        self.error_label.setFont(QFont("Arial", 14))
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label)
        
        # Unlock button
        unlock_btn = QPushButton(t('screentime.unlock_button'))
        unlock_btn.setFixedWidth(200)
        unlock_btn.clicked.connect(self._check_pin)
        layout.addWidget(unlock_btn, 0, Qt.AlignCenter)
    
    def _check_pin(self):
        """Check entered PIN."""
        entered = self.pin_input.text()
        
        if entered == self.pin_code:
            self.accept()
        else:
            self.error_label.setText(t('settings.pin_dialog.incorrect_msg'))
            self.pin_input.clear()
            self.pin_input.setFocus()


class ScreenTimeManager(QWidget):
    """Manages screen time limits and reminders."""
    
    time_updated = pyqtSignal(int, int)  # Emits (remaining_seconds, total_seconds)
    timer_stopped = pyqtSignal()  # Emits when timer stops
    
    def __init__(self, parent_widget: QWidget):
        """Initialize screen time manager.
        
        Args:
            parent_widget: Parent widget for dialogs
        """
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        
        # Initialize controller for daily allowances and usage times
        self.controller = ScreenTimeController(parent_widget)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)
        
        self.start_time: Optional[datetime] = None
        self.elapsed_seconds = 0
        self.is_paused = False
        self.is_locked = False
        
        self.load_settings()
    
    def load_settings(self):
        """Load screentime settings from JSON."""
        try:
            with open(self.settings_path) as f:
                settings = json.load(f)
                st = settings.get("screentime", {})
                
                self.enabled = st.get("enabled", False)
                self.limit_minutes = st.get("limit_minutes", 60)
                self.reminders = st.get("reminders", [30, 5])  # Minutes before end
                self.pin_code = settings.get("parental", {}).get("pin_code", "1234")
                
                self.shown_reminders = set()
        except Exception as e:
            print(f"Error loading screentime settings: {e}")
            self.enabled = False
            self.limit_minutes = 60
            self.reminders = [30, 5]
            self.pin_code = "1234"
            self.shown_reminders = set()
    
    def start(self):
        """Start screen time tracking."""
        # Check if access is allowed
        can_start, reason = self.controller.can_start_session()
        if not can_start:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.parent_widget,
                "Zugriff verweigert",
                reason or "App kann jetzt nicht gestartet werden."
            )
            return
        
        if not self.enabled or self.is_locked:
            return
        
        # Get remaining time for today
        today = date.today()
        remaining_minutes = self.controller.get_remaining_minutes_for_day(today)
        
        # Set limit to remaining time for today
        self.limit_minutes = min(self.limit_minutes, remaining_minutes)
        
        self.start_time = datetime.now()
        self.elapsed_seconds = 0
        self.shown_reminders.clear()
        self.timer.start(1000)  # Update every second
    
    def stop(self):
        """Stop screen time tracking."""
        was_running = self.timer.isActive()
        
        # Save used time if timer was running
        if was_running and self.elapsed_seconds > 0:
            used_minutes = self.elapsed_seconds // 60
            if self.elapsed_seconds % 60 >= 30:  # Round up if 30+ seconds
                used_minutes += 1
            
            today = date.today()
            self.controller.add_used_time(used_minutes, today)
        
        self.timer.stop()
        if was_running:
            self.timer_stopped.emit()
    
    def pause(self):
        """Pause timer."""
        self.is_paused = True
    
    def resume(self):
        """Resume timer."""
        self.is_paused = False
    
    def _on_timer_tick(self):
        """Handle timer tick (every second)."""
        if self.is_paused or self.is_locked:
            return
        
        self.elapsed_seconds += 1
        remaining_seconds = (self.limit_minutes * 60) - self.elapsed_seconds
        total_seconds = self.limit_minutes * 60
        
        # Emit signal for UI updates
        self.time_updated.emit(remaining_seconds, total_seconds)
        
        # Check for reminders (skip first 5 seconds to avoid false triggers on startup)
        if self.elapsed_seconds >= 5:
            remaining_minutes = remaining_seconds // 60
            
            for reminder_minutes in self.reminders:
                if remaining_minutes == reminder_minutes and reminder_minutes not in self.shown_reminders:
                    self.shown_reminders.add(reminder_minutes)
                    self._show_reminder(reminder_minutes)
                    break
        
        # Check if time is up
        if remaining_seconds <= 0:
            self._lock_screen()
    
    def _show_reminder(self, remaining_minutes: int):
        """Show reminder dialog.
        
        Args:
            remaining_minutes: Minutes remaining
        """
        self.pause()
        
        dialog = ReminderDialog(remaining_minutes, self.limit_minutes, self.parent_widget)
        dialog.exec_()
        
        self.resume()
    
    def _lock_screen(self):
        """Lock the screen."""
        self.stop()
        self.is_locked = True
        
        # Show lock dialog
        dialog = LockDialog(self.pin_code, self.parent_widget)
        
        if dialog.exec_() == QDialog.Accepted:
            # PIN correct - unlock and reset
            self.is_locked = False
            self.start()  # Restart timer
        else:
            # Keep locked
            self._lock_screen()
    
    def get_remaining_time(self) -> int:
        """Get remaining time in seconds.
        
        Returns:
            Remaining seconds
        """
        remaining_seconds = (self.limit_minutes * 60) - self.elapsed_seconds
        if remaining_seconds < 0:
            remaining_seconds = 0
        
        return remaining_seconds
    
    def is_running(self) -> bool:
        """Check if timer is running.
        
        Returns:
            True if timer is active
        """
        return self.timer.isActive() and self.enabled
    
    def add_time(self, minutes: int):
        """Add time to current session.
        
        Args:
            minutes: Minutes to add
        """
        # Reduce elapsed seconds to add time
        self.elapsed_seconds -= (minutes * 60)
        if self.elapsed_seconds < 0:
            self.elapsed_seconds = 0
    
    def stop(self):
        """Stop the screen time timer."""
        self.timer.stop()
        self.timer_stopped.emit()
