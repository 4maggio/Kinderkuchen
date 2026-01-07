"""
Parental Settings Dialog

PIN-protected settings for parents to configure the calendar app.
Includes weather location, year view options, sync settings, etc.
"""

import json
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QSpinBox, QMessageBox, QCompleter,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from utils.location import get_location_from_ip
from utils.weather_api import WeatherAPI
from utils.i18n import t, set_language, get_available_languages


class SettingsDialog(QDialog):
    """Parental settings dialog."""
    
    settings_changed = pyqtSignal()  # Emitted when settings are saved
    
    def __init__(self, database, parent=None):
        """Initialize settings dialog.
        
        Args:
            database: CalendarDatabase instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.database = database
        self.settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        self.settings = self._load_settings()
        self.authenticated = False
        
        # Set language from settings
        language = self.settings.get("language", "de")
        set_language(language)
        
        # For location search
        self.location_search_timer = QTimer()
        self.location_search_timer.setSingleShot(True)
        self.location_search_timer.timeout.connect(self._perform_location_search)
        self.location_results = []
        
        self.setWindowTitle(t('settings.title'))
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        # Check if PIN is enabled
        if self.settings.get("parental", {}).get("pin_enabled", False):
            self._show_pin_dialog()
        else:
            self.authenticated = True
            self._init_ui()
    
    def _load_settings(self) -> dict:
        """Load settings from JSON file.
        
        Returns:
            Settings dictionary
        """
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self._get_default_settings()
    
    def _get_default_settings(self) -> dict:
        """Get default settings structure.
        
        Returns:
            Default settings dict
        """
        return {
            "language": "de",
            "weather": {
                "location_mode": "auto",
                "manual_location": "",
                "latitude": None,
                "longitude": None,
                "timezone": "Europe/London"
            },
            "year_view": {
                "start_month_mode": "current",
                "custom_start_month": 1
            },
            "sync": {
                "enabled": False,
                "webcal_url": "",
                "sync_interval_minutes": 30
            },
            "display": {
                "temperature_unit": "celsius",
                "time_format": "24h",
                "unit_system": "metric"
            },
            "screentime": {
                "enabled": False,
                "limit_minutes": 60,
                "reminders": [30, 5],
                "allowed_time_mode": "daily",  # daily, weekly, calendar
                "daily_allowed_minutes": 30,
                "weekly_allowed_minutes": {
                    "monday": 30,
                    "tuesday": 30,
                    "wednesday": 30,
                    "thursday": 30,
                    "friday": 30,
                    "saturday": 60,
                    "sunday": 60
                },
                "calendar_category": "Screentime",
                "usage_times_mode": "always",  # always, weekly, calendar
                "daily_usage_times": {"start": "00:00", "end": "23:59"},
                "weekly_usage_times": {
                    "monday": {"start": "14:00", "end": "20:00"},
                    "tuesday": {"start": "14:00", "end": "20:00"},
                    "wednesday": {"start": "14:00", "end": "20:00"},
                    "thursday": {"start": "14:00", "end": "20:00"},
                    "friday": {"start": "14:00", "end": "21:00"},
                    "saturday": {"start": "09:00", "end": "21:00"},
                    "sunday": {"start": "09:00", "end": "21:00"}
                }
            },
            "appearance": {
                "font_size": 12,
                "font_family": "Arial",
                "theme": "dark"
            },
            "parental": {
                "pin_code": "1234",
                "pin_enabled": False
            }
        }
    
    def _save_settings(self):
        """Save settings to JSON file."""
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
            print("Settings saved successfully")
        except Exception as e:
            print(f"Error saving settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")
    
    def _show_pin_dialog(self):
        """Show PIN entry dialog."""
        pin_dialog = QDialog(self)
        pin_dialog.setWindowTitle(t('settings.pin_dialog.title'))
        pin_dialog.setModal(True)
        
        layout = QVBoxLayout(pin_dialog)
        
        label = QLabel(t('settings.pin_dialog.prompt'))
        label.setFont(QFont("Arial", 14))
        layout.addWidget(label)
        
        pin_input = QLineEdit()
        pin_input.setEchoMode(QLineEdit.Password)
        pin_input.setFont(QFont("Arial", 16))
        pin_input.setMaxLength(6)
        layout.addWidget(pin_input)
        
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton(t('settings.pin_dialog.ok'))
        ok_btn.clicked.connect(lambda: self._verify_pin(pin_input.text(), pin_dialog))
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton(t('settings.pin_dialog.cancel'))
        cancel_btn.clicked.connect(lambda: (pin_dialog.reject(), self.reject()))
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        pin_dialog.exec_()
    
    def _verify_pin(self, entered_pin: str, dialog: QDialog):
        """Verify entered PIN.
        
        Args:
            entered_pin: PIN entered by user
            dialog: PIN dialog to close on success
        """
        correct_pin = self.settings.get("parental", {}).get("pin_code", "1234")
        
        if entered_pin == correct_pin:
            self.authenticated = True
            dialog.accept()
            self._init_ui()
        else:
            QMessageBox.warning(dialog, t('settings.pin_dialog.incorrect'), t('settings.pin_dialog.incorrect_msg'))
    
    def _init_ui(self):
        """Initialize the settings UI."""
        if not self.authenticated:
            return
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #34495E;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QCheckBox {
                color: white;
                font-size: 12px;
            }
            QPushButton {
                background-color: #1ABC9C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16A085;
            }
            QPushButton:pressed {
                background-color: #138D75;
            }
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 2px solid #34495E;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #34495E;
                background-color: #2C3E50;
            }
            QTabBar::tab {
                background-color: #34495E;
                color: white;
                padding: 10px 20px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #1ABC9C;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(t('settings.title'))
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Tabs for different setting categories
        tabs = QTabWidget()
        
        tabs.addTab(self._create_weather_tab(), t('settings.tabs.weather'))
        tabs.addTab(self._create_display_tab(), t('settings.tabs.display'))
        tabs.addTab(self._create_screentime_tab(), "⏱ " + t('screentime.group'))
        tabs.addTab(self._create_appearance_tab(), "🎨 " + t('settings.appearance_tab.title'))
        tabs.addTab(self._create_sync_tab(), t('settings.tabs.sync'))
        tabs.addTab(self._create_security_tab(), t('settings.tabs.security'))
        
        layout.addWidget(tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton(t('settings.save_close'))
        save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton(t('settings.cancel'))
        cancel_btn.setStyleSheet("background-color: #E74C3C;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_weather_tab(self) -> QWidget:
        """Create weather settings tab.
        
        Returns:
            Weather settings widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox(t('settings.weather_tab.location_group'))
        form = QFormLayout()
        
        # Location mode
        self.location_mode = QComboBox()
        self.location_mode.addItems([
            t('settings.weather_tab.location_mode_auto'),
            t('settings.weather_tab.location_mode_manual')
        ])
        current_mode = self.settings.get("weather", {}).get("location_mode", "auto")
        self.location_mode.setCurrentIndex(0 if current_mode == "auto" else 1)
        self.location_mode.currentIndexChanged.connect(self._on_location_mode_changed)
        form.addRow(t('settings.weather_tab.location_mode'), self.location_mode)
        
        # Manual location input with search
        self.manual_location = QLineEdit()
        self.manual_location.setPlaceholderText(t('settings.weather_tab.city_placeholder'))
        self.manual_location.setText(self.settings.get("weather", {}).get("manual_location", ""))
        self.manual_location.textChanged.connect(self._on_location_text_changed)
        form.addRow(t('settings.weather_tab.city_name'), self.manual_location)
        
        # Location search results list
        self.location_list = QListWidget()
        self.location_list.setMaximumHeight(150)
        self.location_list.itemClicked.connect(self._on_location_selected)
        self.location_list.hide()
        form.addRow("", self.location_list)
        
        # Detect location button
        detect_btn = QPushButton(t('settings.weather_tab.detect_location'))
        detect_btn.clicked.connect(self._detect_location)
        form.addRow("", detect_btn)
        
        # Current location display
        self.current_location_label = QLabel(t('settings.weather_tab.current_location'))
        self.current_location_label.setStyleSheet("color: #1ABC9C; font-style: italic;")
        form.addRow("", self.current_location_label)
        
        group.setLayout(form)
        layout.addWidget(group)
        
        # Update UI based on mode
        self._on_location_mode_changed(self.location_mode.currentIndex())
        
        layout.addStretch()
        return widget
    
    def _create_display_tab(self) -> QWidget:
        """Create display settings tab.
        
        Returns:
            Display settings widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Language & Format
        group1 = QGroupBox(t('settings.display_tab.language_group'))
        form1 = QFormLayout()
        
        # Language selection
        self.language_combo = QComboBox()
        available_langs = get_available_languages()
        for lang_code, lang_name in available_langs.items():
            self.language_combo.addItem(lang_name, lang_code)
        current_lang = self.settings.get("language", "de")
        lang_index = list(available_langs.keys()).index(current_lang) if current_lang in available_langs else 0
        self.language_combo.setCurrentIndex(lang_index)
        form1.addRow(t('settings.display_tab.language'), self.language_combo)
        
        # Time format
        self.time_format = QComboBox()
        self.time_format.addItems([
            t('settings.display_tab.time_format_24h'),
            t('settings.display_tab.time_format_12h')
        ])
        current_time = self.settings.get("display", {}).get("time_format", "24h")
        self.time_format.setCurrentIndex(0 if current_time == "24h" else 1)
        form1.addRow(t('settings.display_tab.time_format'), self.time_format)
        
        group1.setLayout(form1)
        layout.addWidget(group1)
        
        # Temperature unit
        group2 = QGroupBox(t('settings.display_tab.temperature_group'))
        form2 = QFormLayout()
        
        self.temp_unit = QComboBox()
        self.temp_unit.addItems([
            t('settings.display_tab.temperature_celsius'),
            t('settings.display_tab.temperature_fahrenheit')
        ])
        current_unit = self.settings.get("display", {}).get("temperature_unit", "celsius")
        self.temp_unit.setCurrentIndex(0 if current_unit == "celsius" else 1)
        form2.addRow(t('settings.display_tab.temperature_unit'), self.temp_unit)
        
        group2.setLayout(form2)
        layout.addWidget(group2)
        
        # Measurement units
        group3 = QGroupBox(t('settings.display_tab.units_group'))
        form3 = QFormLayout()
        
        self.unit_system = QComboBox()
        self.unit_system.addItems([
            t('settings.display_tab.unit_system_metric'),
            t('settings.display_tab.unit_system_imperial')
        ])
        current_system = self.settings.get("display", {}).get("unit_system", "metric")
        self.unit_system.setCurrentIndex(0 if current_system == "metric" else 1)
        form3.addRow(t('settings.display_tab.unit_system'), self.unit_system)
        
        group3.setLayout(form3)
        layout.addWidget(group3)
        
        # Year view settings
        group4 = QGroupBox(t('settings.display_tab.year_view_group'))
        form4 = QFormLayout()
        
        self.year_start_mode = QComboBox()
        self.year_start_mode.addItems([
            t('settings.display_tab.year_start_current'),
            t('settings.display_tab.year_start_january'),
            t('settings.display_tab.year_start_custom')
        ])
        current_mode = self.settings.get("year_view", {}).get("start_month_mode", "current")
        mode_index = {"current": 0, "january": 1, "custom": 2}.get(current_mode, 0)
        self.year_start_mode.setCurrentIndex(mode_index)
        self.year_start_mode.currentIndexChanged.connect(self._on_year_mode_changed)
        form4.addRow(t('settings.display_tab.year_start_mode'), self.year_start_mode)
        
        self.custom_month = QComboBox()
        month_names = [t(f'year_view.{month}') for month in [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december"
        ]]
        self.custom_month.addItems(month_names)
        custom_month_num = self.settings.get("year_view", {}).get("custom_start_month", 1)
        self.custom_month.setCurrentIndex(custom_month_num - 1)
        form4.addRow(t('settings.display_tab.custom_month'), self.custom_month)
        
        group4.setLayout(form4)
        layout.addWidget(group4)
        
        self._on_year_mode_changed(self.year_start_mode.currentIndex())
        
        layout.addStretch()
        return widget
    
    def _create_sync_tab(self) -> QWidget:
        """Create sync settings tab.
        
        Returns:
            Sync settings widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Calendar Sync (Future Feature)")
        form = QFormLayout()
        
        self.sync_enabled = QCheckBox("Enable calendar sync")
        self.sync_enabled.setChecked(self.settings.get("sync", {}).get("enabled", False))
        form.addRow("", self.sync_enabled)
        
        self.webcal_url = QLineEdit()
        self.webcal_url.setPlaceholderText(t('settings.sync_tab.webcal_placeholder'))
        self.webcal_url.setText(self.settings.get("sync", {}).get("webcal_url", ""))
        form.addRow(t('settings.sync_tab.webcal_url'), self.webcal_url)
        
        self.sync_interval = QSpinBox()
        self.sync_interval.setRange(5, 120)
        self.sync_interval.setSuffix(" minutes")
        self.sync_interval.setValue(self.settings.get("sync", {}).get("sync_interval_minutes", 30))
        form.addRow(t('settings.sync_tab.sync_interval'), self.sync_interval)
        
        note = QLabel(t('settings.sync_tab.note'))
        note.setStyleSheet("color: #E67E22; font-style: italic; font-size: 11px;")
        form.addRow("", note)
        
        group.setLayout(form)
        layout.addWidget(group)
        
        layout.addStretch()
        return widget
    
    def _create_screentime_tab(self) -> QWidget:
        """Create screen time settings tab.
        
        Returns:
            Screen time settings widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Enable/Disable Group
        enable_group = QGroupBox(t('screentime.group'))
        enable_form = QFormLayout()
        
        self.screentime_enabled = QCheckBox(t('screentime.enabled'))
        self.screentime_enabled.setChecked(self.settings.get("screentime", {}).get("enabled", False))
        enable_form.addRow("", self.screentime_enabled)
        
        enable_group.setLayout(enable_form)
        layout.addWidget(enable_group)
        
        # Daily Limit Group
        limit_group = QGroupBox("Tageslimit")
        limit_form = QFormLayout()
        
        self.screentime_limit = QSpinBox()
        self.screentime_limit.setMinimum(5)
        self.screentime_limit.setMaximum(480)
        self.screentime_limit.setSuffix(" min")
        self.screentime_limit.setValue(self.settings.get("screentime", {}).get("limit_minutes", 60))
        limit_form.addRow(t('screentime.limit_minutes'), self.screentime_limit)
        
        limit_group.setLayout(limit_form)
        layout.addWidget(limit_group)
        
        # Reminders Group
        reminder_group = QGroupBox(t('screentime.reminders'))
        reminder_layout = QVBoxLayout()
        
        self.reminders_list = QListWidget()
        self.reminders_list.setMaximumHeight(80)
        
        reminders = self.settings.get("screentime", {}).get("reminders", [30, 5])
        for reminder in reminders:
            self.reminders_list.addItem(f"{reminder} min")
        
        reminder_layout.addWidget(self.reminders_list)
        
        reminder_btn_layout = QHBoxLayout()
        add_reminder_btn = QPushButton("+ " + t('screentime.add_reminder'))
        add_reminder_btn.clicked.connect(self._add_reminder)
        reminder_btn_layout.addWidget(add_reminder_btn)
        
        remove_reminder_btn = QPushButton("- " + t('common.delete'))
        remove_reminder_btn.clicked.connect(self._remove_reminder)
        reminder_btn_layout.addWidget(remove_reminder_btn)
        
        reminder_layout.addLayout(reminder_btn_layout)
        reminder_group.setLayout(reminder_layout)
        layout.addWidget(reminder_group)
        
        # Allowed Time Mode Group
        allowed_group = QGroupBox("Erlaubte Bildschirmzeit pro Tag")
        allowed_form = QFormLayout()
        
        self.allowed_time_mode = QComboBox()
        self.allowed_time_mode.addItem("Täglich gleich", "daily")
        self.allowed_time_mode.addItem("Wochenplan", "weekly")
        self.allowed_time_mode.addItem("Kalenderbasiert", "calendar")
        
        current_mode = self.settings.get("screentime", {}).get("allowed_time_mode", "daily")
        mode_index = self.allowed_time_mode.findData(current_mode)
        if mode_index >= 0:
            self.allowed_time_mode.setCurrentIndex(mode_index)
        
        allowed_form.addRow("Modus:", self.allowed_time_mode)
        
        self.daily_allowed = QSpinBox()
        self.daily_allowed.setMinimum(0)
        self.daily_allowed.setMaximum(480)
        self.daily_allowed.setSuffix(" min")
        self.daily_allowed.setValue(self.settings.get("screentime", {}).get("daily_allowed_minutes", 30))
        allowed_form.addRow("Täglich erlaubt:", self.daily_allowed)
        
        allowed_group.setLayout(allowed_form)
        layout.addWidget(allowed_group)
        
        # Usage Times Group
        usage_group = QGroupBox("Erlaubte Nutzungszeiten")
        usage_form = QFormLayout()
        
        self.usage_times_mode = QComboBox()
        self.usage_times_mode.addItem("Immer verfügbar", "always")
        self.usage_times_mode.addItem("Wochenplan", "weekly")
        self.usage_times_mode.addItem("Kalenderbasiert", "calendar")
        
        current_usage_mode = self.settings.get("screentime", {}).get("usage_times_mode", "always")
        usage_index = self.usage_times_mode.findData(current_usage_mode)
        if usage_index >= 0:
            self.usage_times_mode.setCurrentIndex(usage_index)
        
        usage_form.addRow("Modus:", self.usage_times_mode)
        
        usage_group.setLayout(usage_form)
        layout.addWidget(usage_group)
        
        layout.addStretch()
        return widget
    
    def _add_reminder(self):
        """Add a reminder to the list."""
        # Simple dialog for minutes
        from PyQt5.QtWidgets import QInputDialog
        
        minutes, ok = QInputDialog.getInt(
            self,
            t('screentime.add_reminder'),
            t('screentime.limit_minutes'),
            30,  # Default
            1,   # Min
            self.screentime_limit.value() - 1  # Max (less than total time)
        )
        
        if ok:
            self.reminders_list.addItem(f"{minutes} min")
    
    def _remove_reminder(self):
        """Remove selected reminder."""
        current_item = self.reminders_list.currentItem()
        if current_item:
            self.reminders_list.takeItem(self.reminders_list.row(current_item))
    
    def _create_security_tab(self) -> QWidget:
        """Create security settings tab.
        
        Returns:
            Security settings widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox(t('settings.security_tab.pin_group'))
        form = QFormLayout()
        
        self.pin_enabled = QCheckBox(t('settings.security_tab.pin_enabled'))
        self.pin_enabled.setChecked(self.settings.get("parental", {}).get("pin_enabled", False))
        form.addRow("", self.pin_enabled)
        
        self.pin_code = QLineEdit()
        self.pin_code.setEchoMode(QLineEdit.Password)
        self.pin_code.setMaxLength(6)
        self.pin_code.setPlaceholderText(t('settings.security_tab.pin_placeholder'))
        self.pin_code.setText(self.settings.get("parental", {}).get("pin_code", "1234"))
        form.addRow(t('settings.security_tab.pin_code'), self.pin_code)
        
        warning = QLabel(t('settings.security_tab.pin_warning'))
        warning.setStyleSheet("color: #E67E22; font-size: 11px;")
        form.addRow("", warning)
        
        group.setLayout(form)
        layout.addWidget(group)
        
        layout.addStretch()
        return widget
    
    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab.
        
        Returns:
            Appearance settings widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Font settings
        font_group = QGroupBox(t('settings.appearance_tab.font_group'))
        font_form = QFormLayout()
        
        # Font size
        self.font_size = QSpinBox()
        self.font_size.setMinimum(8)
        self.font_size.setMaximum(24)
        self.font_size.setValue(self.settings.get("appearance", {}).get("font_size", 12))
        font_form.addRow(t('settings.appearance_tab.font_size'), self.font_size)
        
        # Font family
        self.font_family = QComboBox()
        self.font_family.addItems(["Arial", "Helvetica", "Verdana", "Tahoma", "Trebuchet MS", "Comic Sans MS"])
        current_font = self.settings.get("appearance", {}).get("font_family", "Arial")
        index = self.font_family.findText(current_font)
        if index >= 0:
            self.font_family.setCurrentIndex(index)
        font_form.addRow(t('settings.appearance_tab.font_family'), self.font_family)
        
        font_group.setLayout(font_form)
        layout.addWidget(font_group)
        
        # Theme settings
        theme_group = QGroupBox(t('settings.appearance_tab.theme_group'))
        theme_form = QFormLayout()
        
        self.theme = QComboBox()
        self.theme.addItem(t('settings.appearance_tab.theme_dark'), "dark")
        self.theme.addItem(t('settings.appearance_tab.theme_light'), "light")
        self.theme.addItem(t('settings.appearance_tab.theme_blue'), "blue")
        self.theme.addItem(t('settings.appearance_tab.theme_green'), "green")
        
        current_theme = self.settings.get("appearance", {}).get("theme", "dark")
        theme_index = self.theme.findData(current_theme)
        if theme_index >= 0:
            self.theme.setCurrentIndex(theme_index)
        
        theme_form.addRow(t('settings.appearance_tab.theme'), self.theme)
        
        theme_group.setLayout(theme_form)
        layout.addWidget(theme_group)
        
        layout.addStretch()
        return widget
    
    def _on_location_mode_changed(self, index: int):
        """Handle location mode change.
        
        Args:
            index: Selected index (0=auto, 1=manual)
        """
        is_manual = (index == 1)
        self.manual_location.setEnabled(is_manual)
        self.location_list.setEnabled(is_manual)
    
    def _on_location_text_changed(self, text: str):
        """Handle location text change - trigger search with delay.
        
        Args:
            text: Current text in location field
        """
        if len(text) < 2:
            self.location_list.clear()
            self.location_list.hide()
            return
        
        # Restart timer - wait for user to stop typing
        self.location_search_timer.stop()
        self.location_search_timer.start(500)  # 500ms delay
    
    def _perform_location_search(self):
        """Perform location search via Open-Meteo API."""
        query = self.manual_location.text().strip()
        
        if len(query) < 2:
            return
        
        # Show loading indicator
        self.location_list.clear()
        loading_item = QListWidgetItem(t('settings.weather_tab.searching'))
        loading_item.setFlags(Qt.NoItemFlags)
        self.location_list.addItem(loading_item)
        self.location_list.show()
        
        # Perform search
        self.location_results = WeatherAPI.search_locations(query, count=10)
        
        # Update list
        self.location_list.clear()
        
        if not self.location_results:
            no_results = QListWidgetItem(t('settings.weather_tab.no_results'))
            no_results.setFlags(Qt.NoItemFlags)
            self.location_list.addItem(no_results)
        else:
            for i, location in enumerate(self.location_results):
                item = QListWidgetItem(location['display_name'])
                item.setData(Qt.UserRole, i)  # Store index
                self.location_list.addItem(item)
        
        self.location_list.show()
    
    def _on_location_selected(self, item: QListWidgetItem):
        """Handle location selection from search results.
        
        Args:
            item: Selected list item
        """
        index = item.data(Qt.UserRole)
        
        if index is None:
            return
        
        location = self.location_results[index]
        
        # Update text field with city name
        self.manual_location.setText(location['name'])
        
        # Store coordinates in settings
        self.settings["weather"]["latitude"] = location['latitude']
        self.settings["weather"]["longitude"] = location['longitude']
        self.settings["weather"]["timezone"] = location['timezone']
        self.settings["weather"]["manual_location"] = location['name']
        
        # Update display
        self.current_location_label.setText(
            t('settings.weather_tab.selected_location', 
              location=location['display_name'], 
              lat=location['latitude'], 
              lon=location['longitude'])
        )
        
        # Hide list
        self.location_list.hide()
    
    def _on_year_mode_changed(self, index: int):
        """Handle year view mode change.
        
        Args:
            index: Selected index (0=current, 1=january, 2=custom)
        """
        is_custom = (index == 2)
        self.custom_month.setEnabled(is_custom)
    
    def _detect_location(self):
        """Detect location from IP address."""
        location = get_location_from_ip()
        
        if location:
            lat, lon, city, tz = location
            self.current_location_label.setText(
                t('settings.weather_tab.selected_location',
                  location=city,
                  lat=lat,
                  lon=lon)
            )
            
            # Update settings
            self.settings["weather"]["latitude"] = lat
            self.settings["weather"]["longitude"] = lon
            self.settings["weather"]["manual_location"] = city
            self.settings["weather"]["timezone"] = tz
            
            QMessageBox.information(
                self, 
                t('settings.weather_tab.detect_success'), 
                t('settings.weather_tab.detect_success_msg', city=city)
            )
        else:
            QMessageBox.warning(
                self, 
                t('settings.weather_tab.detect_failed'), 
                t('settings.weather_tab.detect_failed_msg')
            )
    
    def _save_and_close(self):
        """Save settings and close dialog."""
        # Update language
        lang_code = self.language_combo.currentData()
        if lang_code:
            self.settings["language"] = lang_code
            set_language(lang_code)
        
        # Update weather settings
        self.settings["weather"]["location_mode"] = "auto" if self.location_mode.currentIndex() == 0 else "manual"
        self.settings["weather"]["manual_location"] = self.manual_location.text()
        
        # Update display settings
        self.settings["display"]["temperature_unit"] = "celsius" if self.temp_unit.currentIndex() == 0 else "fahrenheit"
        self.settings["display"]["time_format"] = "24h" if self.time_format.currentIndex() == 0 else "12h"
        self.settings["display"]["unit_system"] = "metric" if self.unit_system.currentIndex() == 0 else "imperial"
        
        # Update year view settings
        year_modes = ["current", "january", "custom"]
        self.settings["year_view"]["start_month_mode"] = year_modes[self.year_start_mode.currentIndex()]
        self.settings["year_view"]["custom_start_month"] = self.custom_month.currentIndex() + 1
        
        # Update sync settings
        self.settings["sync"]["enabled"] = self.sync_enabled.isChecked()
        self.settings["sync"]["webcal_url"] = self.webcal_url.text()
        self.settings["sync"]["sync_interval_minutes"] = self.sync_interval.value()
        
        # Update parental settings
        self.settings["parental"]["pin_enabled"] = self.pin_enabled.isChecked()
        self.settings["parental"]["pin_code"] = self.pin_code.text()
        
        # Update screentime settings
        if "screentime" not in self.settings:
            self.settings["screentime"] = {}
        
        self.settings["screentime"]["enabled"] = self.screentime_enabled.isChecked()
        self.settings["screentime"]["limit_minutes"] = self.screentime_limit.value()
        
        # Parse reminders from list
        reminders = []
        for i in range(self.reminders_list.count()):
            item_text = self.reminders_list.item(i).text()
            minutes = int(item_text.split()[0])
            reminders.append(minutes)
        self.settings["screentime"]["reminders"] = sorted(reminders, reverse=True)
        
        # Save new screentime settings
        self.settings["screentime"]["allowed_time_mode"] = self.allowed_time_mode.currentData()
        self.settings["screentime"]["daily_allowed_minutes"] = self.daily_allowed.value()
        self.settings["screentime"]["usage_times_mode"] = self.usage_times_mode.currentData()
        
        # Update appearance settings
        if "appearance" not in self.settings:
            self.settings["appearance"] = {}
        
        self.settings["appearance"]["font_size"] = self.font_size.value()
        self.settings["appearance"]["font_family"] = self.font_family.currentText()
        self.settings["appearance"]["theme"] = self.theme.currentData()
        
        # Save to file
        self._save_settings()
        
        # Emit signal
        self.settings_changed.emit()
        
        # Close dialog
        self.accept()
