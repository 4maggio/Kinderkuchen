"""Screen time quick actions dialog.

Shows remaining time with analog clock and quick action buttons.
"""

import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from utils.i18n import t
from utils.screentime import AnalogClockWidget


class ScreenTimeQuickActionsDialog(QDialog):
    """Dialog for screen time quick actions and management."""
    
    time_added = pyqtSignal(int)  # Emits minutes added
    timer_cancelled = pyqtSignal()  # Emits when timer cancelled
    credit_tomorrow = pyqtSignal(int)  # Emits minutes to credit for tomorrow
    
    def __init__(self, remaining_seconds: int, total_seconds: int, parent=None):
        """Initialize quick actions dialog.
        
        Args:
            remaining_seconds: Remaining screen time in seconds
            total_seconds: Total screen time limit in seconds
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.remaining_seconds = remaining_seconds
        self.total_seconds = total_seconds
        self.pin_code = self._load_pin()
        
        self._init_ui()
    
    def _load_pin(self) -> str:
        """Load PIN from settings.
        
        Returns:
            PIN code string
        """
        settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        try:
            with open(settings_path) as f:
                settings = json.load(f)
                return settings.get("parental", {}).get("pin_code", "1234")
        except:
            return "1234"
    
    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(t('screentime.quick_actions_title'))
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Set to fullscreen
        if self.parent():
            self.setGeometry(self.parent().geometry())
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #34495E;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3E5161;
            }
            QPushButton:pressed {
                background-color: #1ABC9C;
            }
            QPushButton#cancel_btn {
                background-color: #E74C3C;
            }
            QPushButton#cancel_btn:hover {
                background-color: #C0392B;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel(t('screentime.quick_actions_title'))
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Analog clock
        self.clock = AnalogClockWidget(self.remaining_seconds)
        self.clock.set_remaining(self.remaining_seconds, self.total_seconds)
        self.clock.setFixedSize(350, 350)
        clock_container = QHBoxLayout()
        clock_container.addStretch()
        clock_container.addWidget(self.clock)
        clock_container.addStretch()
        layout.addLayout(clock_container)
        
        # Remaining time text
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.time_label = QLabel(t('screentime.remaining_label', time=time_str))
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.time_label)
        
        # Quick action buttons grid
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Row 1: Add time buttons
        add_5_btn = QPushButton(t('screentime.add_5_min'))
        add_5_btn.clicked.connect(lambda: self._add_time(5))
        grid.addWidget(add_5_btn, 0, 0)
        
        add_15_btn = QPushButton(t('screentime.add_15_min'))
        add_15_btn.clicked.connect(lambda: self._add_time(15))
        grid.addWidget(add_15_btn, 0, 1)
        
        add_30_btn = QPushButton(t('screentime.add_30_min'))
        add_30_btn.clicked.connect(lambda: self._add_time(30))
        grid.addWidget(add_30_btn, 0, 2)
        
        # Row 2: Tomorrow credit buttons
        credit_btn = QPushButton(t('screentime.credit_tomorrow'))
        credit_btn.clicked.connect(self._credit_remaining_tomorrow)
        grid.addWidget(credit_btn, 1, 0)
        
        remaining_btn = QPushButton(t('screentime.remaining_to_tomorrow'))
        remaining_btn.clicked.connect(self._move_remaining_tomorrow)
        grid.addWidget(remaining_btn, 1, 1)
        
        double_btn = QPushButton(t('screentime.double_tomorrow'))
        double_btn.clicked.connect(self._double_tomorrow)
        grid.addWidget(double_btn, 1, 2)
        
        layout.addLayout(grid)
        
        # Cancel timer button (requires PIN)
        cancel_btn = QPushButton(t('screentime.cancel_timer'))
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self._cancel_timer)
        layout.addWidget(cancel_btn)
    
    def update_time(self, remaining_seconds: int, total_seconds: int):
        """Update the displayed time.
        
        Args:
            remaining_seconds: Remaining seconds
            total_seconds: Total seconds
        """
        self.remaining_seconds = remaining_seconds
        self.total_seconds = total_seconds
        
        self.clock.set_remaining(remaining_seconds, total_seconds)
        
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.time_label.setText(t('screentime.remaining_label', time=time_str))
    
    def _add_time(self, minutes: int):
        """Add time to current session.
        
        Args:
            minutes: Minutes to add
        """
        self.time_added.emit(minutes)
        QMessageBox.information(
            self,
            t('common.ok'),
            f"{minutes}{t('screentime.minutes_suffix')} hinzugefügt!"
        )
        self.accept()
    
    def _credit_remaining_tomorrow(self):
        """Credit remaining time for tomorrow."""
        minutes = self.remaining_seconds // 60
        self.credit_tomorrow.emit(minutes)
        QMessageBox.information(
            self,
            t('common.ok'),
            f"{minutes}{t('screentime.minutes_suffix')} für morgen gutgeschrieben!"
        )
    
    def _move_remaining_tomorrow(self):
        """Move remaining time to tomorrow and end session."""
        minutes = self.remaining_seconds // 60
        self.credit_tomorrow.emit(minutes)
        self.timer_cancelled.emit()
        QMessageBox.information(
            self,
            t('common.ok'),
            f"{minutes}{t('screentime.minutes_suffix')} für morgen gutgeschrieben. Timer beendet."
        )
        self.accept()
    
    def _double_tomorrow(self):
        """Double remaining time for tomorrow."""
        minutes = (self.remaining_seconds // 60) * 2
        self.credit_tomorrow.emit(minutes)
        QMessageBox.information(
            self,
            t('common.ok'),
            f"{minutes}{t('screentime.minutes_suffix')} für morgen gutgeschrieben!"
        )
    
    def _cancel_timer(self):
        """Cancel timer after PIN verification."""
        # PIN dialog
        pin_dialog = QDialog(self)
        pin_dialog.setWindowTitle("PIN")
        pin_dialog.setModal(True)
        pin_dialog.setFixedSize(300, 150)
        
        layout = QVBoxLayout(pin_dialog)
        
        label = QLabel("Eltern-PIN eingeben:")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        pin_input = QLineEdit()
        pin_input.setEchoMode(QLineEdit.Password)
        pin_input.setMaxLength(6)
        pin_input.setAlignment(Qt.AlignCenter)
        pin_input.setFont(QFont("Arial", 18))
        layout.addWidget(pin_input)
        
        btn_layout = QHBoxLayout()
        
        ok_btn = QPushButton(t('common.ok'))
        ok_btn.clicked.connect(pin_dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton(t('common.cancel'))
        cancel_btn.clicked.connect(pin_dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        if pin_dialog.exec_() == QDialog.Accepted:
            if pin_input.text() == self.pin_code:
                self.timer_cancelled.emit()
                QMessageBox.information(
                    self,
                    t('common.ok'),
                    "Timer wurde abgebrochen."
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    "Falscher PIN!"
                )
