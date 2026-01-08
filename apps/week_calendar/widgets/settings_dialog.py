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
    QListWidget, QListWidgetItem, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from utils.location import get_location_from_ip
from utils.weather_api import WeatherAPI
from utils.i18n import t, set_language, get_available_languages
from themes.theme_manager import get_theme_manager, Theme, ThemeColors
from widgets.theme_editor_dialog import ThemeEditorDialog


class SettingsDialog(QWidget):
    """Parental settings view - displayed fullscreen."""
    
    settings_changed = pyqtSignal()  # Emitted when settings are saved
    close_requested = pyqtSignal()  # Emitted when user wants to close settings
    theme_preview_requested = pyqtSignal(str, dict)
    theme_preview_reset = pyqtSignal()
    REPO_URL = "https://github.com/4maggio/Kinderkuchen"
    WEATHER_PROVIDER_URL = "https://open-meteo.com/"
    ARTWORK_CREDIT = "mochi_024"
    
    def __init__(self, database, parent=None, theme: Optional[Theme] = None):
        """Initialize settings view.
        
        Args:
            database: CalendarDatabase instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.database = database
        self.settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        self.settings = self._load_settings()
        self.authenticated = False
        self.theme = theme or self._load_theme_from_settings()
        self.theme_colors = self.theme.colors if self.theme else ThemeColors()
        self.live_preview_checkbox: Optional[QCheckBox] = None
        self.live_preview_enabled = False
        self.tabs: Optional[QTabWidget] = None
        self.prev_tab_button: Optional[QPushButton] = None
        self.next_tab_button: Optional[QPushButton] = None
        self.launcher_apps = list(self.settings.get("launcher", {}).get("apps", []))
        
        # Set language from settings
        language = self.settings.get("language", "de")
        set_language(language)
        
        # For location search
        self.location_search_timer = QTimer()
        self.location_search_timer.setSingleShot(True)
        self.location_search_timer.timeout.connect(self._perform_location_search)
        self.location_results = []
        
        self.setObjectName("SettingsView")
        
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
                "theme": "dark",
                "tile_icon_size": 64,
                "hero_icon_size": 96,
                "calendar_icon_size": 48,
                "font_scale_small": 0,
                "font_scale_large": 50
            },
            "daily_icons": {
                "mode": "always",  # always, weekly, calendar
                "default_icons": ["🏰", "🌟", "🎨"],
                "weekly_icons": {
                    "monday": ["📚", "⚽", "🎵"],
                    "tuesday": ["📚", "⚽", "🎵"],
                    "wednesday": ["📚", "⚽", "🎵"],
                    "thursday": ["📚", "⚽", "🎵"],
                    "friday": ["📚", "⚽", "🎉"],
                    "saturday": ["🎮", "🎨", "🏀"],
                    "sunday": ["🎮", "🎨", "🏀"]
                },
                "calendar_categories": ["School", "Sports", "Music"]
            },
            "launcher": {
                "grid_rows": 2,
                "grid_columns": 2,
                "apps": []
            },
            "parental": {
                "pin_code": "1234",
                "pin_enabled": False
            },
            "vnc": {
                "enabled": False,
                "password": "",
                "view_only_password": ""
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
        cancel_btn.clicked.connect(lambda: (pin_dialog.reject(), self.close_requested.emit()))
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def _apply_theme_styles(self):
        """Apply the current theme palette to dialog widgets."""
        c = self.theme_colors
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c.background};
                color: {c.text_primary};
            }}
            QLabel {{
                color: {c.text_primary};
                font-size: 12px;
            }}
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }}
            QCheckBox {{
                color: {c.text_primary};
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {c.accent};
                color: {c.text_primary};
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c.accent_hover};
            }}
            QPushButton#TabNavButton {{
                min-width: 70px;
                min-height: 70px;
                max-width: 90px;
                max-height: 90px;
                font-size: 28px;
                font-weight: bold;
                border-radius: 18px;
            }}
            QGroupBox {{
                color: {c.text_primary};
                font-weight: bold;
                border: 2px solid {c.border};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QTabWidget::pane {{
                border: 1px solid {c.border};
                background-color: {c.background};
            }}
            QTabBar::tab {{
                background-color: {c.background_secondary};
                color: {c.text_secondary};
                padding: 10px 20px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }}
            QTabBar::tab:selected {{
                background-color: {c.accent};
                color: {c.text_primary};
            }}
            QTabBar QToolButton {{
                background: transparent;
                border: none;
                width: 0px;
                height: 0px;
            }}
            QTabBar::scroller {{
                width: 0px;
            }}
        """)

    def _load_theme_from_settings(self) -> Theme:
        """Resolve the theme referenced in settings for dialog styling."""
        theme_manager = get_theme_manager()
        theme_name = self.settings.get("appearance", {}).get("theme", "dark")
        theme = theme_manager.get_theme(theme_name)
        if theme is None:
            theme = theme_manager.get_theme("dark")
        return theme

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
        
        self._apply_theme_styles()
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(t('settings.title'))
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Tabs for different setting categories
        tabs = QTabWidget()
        tabs.setObjectName("SettingsTabs")
        tab_bar = tabs.tabBar()
        if tab_bar:
            tab_bar.setUsesScrollButtons(False)
        tabs.currentChanged.connect(self._update_tab_nav_buttons)
        self.tabs = tabs
        
        tabs.addTab(self._create_weather_tab(), t('settings.tabs.weather'))
        tabs.addTab(self._create_display_tab(), t('settings.tabs.display'))
        tabs.addTab(self._create_screentime_tab(), "⏱ " + t('screentime.group'))
        tabs.addTab(self._create_daily_icons_tab(), "🎯 Tages-Icons")
        tabs.addTab(self._create_apps_tab(), "🧩 " + t('settings.tabs.apps'))
        tabs.addTab(self._create_appearance_tab(), "🎨 " + t('settings.appearance_tab.title'))
        tabs.addTab(self._create_sync_tab(), t('settings.tabs.sync'))
        tabs.addTab(self._create_security_tab(), t('settings.tabs.security'))
        tabs.addTab(self._create_about_tab(), t('settings.tabs.about'))
        
        nav_row = QHBoxLayout()
        nav_row.setContentsMargins(0, 0, 0, 0)
        nav_row.setSpacing(16)
        self.prev_tab_button = self._create_tab_nav_button("◀")
        self.prev_tab_button.clicked.connect(self._go_to_previous_tab)
        nav_row.addWidget(self.prev_tab_button, 0, Qt.AlignVCenter)
        nav_row.addWidget(tabs, 1)
        self.next_tab_button = self._create_tab_nav_button("▶")
        self.next_tab_button.clicked.connect(self._go_to_next_tab)
        nav_row.addWidget(self.next_tab_button, 0, Qt.AlignVCenter)
        layout.addLayout(nav_row)
        self._update_tab_nav_buttons()
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton(t('settings.save_close'))
        save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton(t('settings.cancel'))
        cancel_btn.setStyleSheet(f"background-color: {self.theme_colors.error};")
        cancel_btn.clicked.connect(self.cancel)
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
        self.current_location_label.setStyleSheet(
            f"color: {self.theme_colors.accent}; font-style: italic;"
        )
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
        note.setStyleSheet(
            f"color: {self.theme_colors.warning}; font-style: italic; font-size: 11px;"
        )
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

    def _create_apps_tab(self) -> QWidget:
        """Create launcher apps configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        launcher = self.settings.get("launcher", {})
        
        grid_group = QGroupBox(t('settings.apps_tab.grid_group'))
        grid_form = QFormLayout()
        self.launcher_grid_rows = QSpinBox()
        self.launcher_grid_rows.setRange(1, 4)
        self.launcher_grid_rows.setValue(launcher.get("grid_rows", 2))
        grid_form.addRow(t('settings.apps_tab.rows'), self.launcher_grid_rows)
        self.launcher_grid_columns = QSpinBox()
        self.launcher_grid_columns.setRange(1, 4)
        self.launcher_grid_columns.setValue(launcher.get("grid_columns", 2))
        grid_form.addRow(t('settings.apps_tab.columns'), self.launcher_grid_columns)
        grid_group.setLayout(grid_form)
        layout.addWidget(grid_group)
        
        apps_group = QGroupBox(t('settings.apps_tab.apps_group'))
        apps_layout = QVBoxLayout()
        hint = QLabel(t('settings.apps_tab.apps_hint'))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {self.theme_colors.text_secondary}; font-size: 11px;")
        apps_layout.addWidget(hint)
        
        self.apps_list = QListWidget()
        self.apps_list.setSelectionMode(QListWidget.SingleSelection)
        apps_layout.addWidget(self.apps_list)
        self._refresh_apps_list()
        
        button_row = QHBoxLayout()
        add_btn = QPushButton("+ " + t('settings.apps_tab.add'))
        add_btn.clicked.connect(self._add_launcher_app)
        button_row.addWidget(add_btn)
        edit_btn = QPushButton(t('settings.apps_tab.edit'))
        edit_btn.clicked.connect(self._edit_launcher_app)
        button_row.addWidget(edit_btn)
        remove_btn = QPushButton("✖ " + t('settings.apps_tab.remove'))
        remove_btn.clicked.connect(self._remove_launcher_app)
        button_row.addWidget(remove_btn)
        button_row.addStretch()
        apps_layout.addLayout(button_row)
        
        apps_group.setLayout(apps_layout)
        layout.addWidget(apps_group)
        layout.addStretch()
        return widget

    def _refresh_apps_list(self):
        if not hasattr(self, 'apps_list'):
            return
        self.apps_list.clear()
        if not self.launcher_apps:
            empty_item = QListWidgetItem(t('settings.apps_tab.empty'))
            empty_item.setFlags(Qt.NoItemFlags)
            self.apps_list.addItem(empty_item)
            return
        for app in self.launcher_apps:
            display_name = app.get("name", t('settings.apps_tab.unnamed'))
            type_label = self._get_app_type_label(app.get("type", "python"))
            item = QListWidgetItem(f"{display_name} · {type_label}")
            item.setData(Qt.UserRole, app)
            self.apps_list.addItem(item)

    def _get_app_type_label(self, app_type: str) -> str:
        labels = {
            "python": t('settings.apps_tab.types.python'),
            "website": t('settings.apps_tab.types.website')
        }
        return labels.get(app_type, app_type)

    def _add_launcher_app(self):
        dialog = AppConfigDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.launcher_apps.append(dialog.app_data)
            self._refresh_apps_list()

    def _edit_launcher_app(self):
        current_item = self.apps_list.currentItem() if hasattr(self, 'apps_list') else None
        if not current_item or current_item.flags() == Qt.NoItemFlags:
            return
        data = current_item.data(Qt.UserRole) or {}
        dialog = AppConfigDialog(parent=self, app_data=data)
        if dialog.exec_() == QDialog.Accepted:
            idx = self.apps_list.row(current_item)
            self.launcher_apps[idx] = dialog.app_data
            self._refresh_apps_list()
            self.apps_list.setCurrentRow(idx)

    def _remove_launcher_app(self):
        current_item = self.apps_list.currentItem() if hasattr(self, 'apps_list') else None
        if not current_item or current_item.flags() == Qt.NoItemFlags:
            return
        idx = self.apps_list.row(current_item)
        del self.launcher_apps[idx]
        self._refresh_apps_list()
    
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
        warning.setStyleSheet(f"color: {self.theme_colors.warning}; font-size: 11px;")
        form.addRow("", warning)
        
        group.setLayout(form)
        layout.addWidget(group)
        
        # VNC Remote Access Group
        vnc_group = QGroupBox("🖥️ RealVNC Fernzugriff")
        vnc_form = QFormLayout()
        
        self.vnc_enabled = QCheckBox("VNC Server aktivieren")
        self.vnc_enabled.setChecked(self.settings.get("vnc", {}).get("enabled", False))
        self.vnc_enabled.toggled.connect(self._on_vnc_enabled_changed)
        vnc_form.addRow("", self.vnc_enabled)
        
        self.vnc_password = QLineEdit()
        self.vnc_password.setEchoMode(QLineEdit.Password)
        self.vnc_password.setPlaceholderText("VNC Passwort (optional)")
        self.vnc_password.setText(self.settings.get("vnc", {}).get("password", ""))
        vnc_form.addRow("VNC Passwort:", self.vnc_password)
        
        self.vnc_view_only_password = QLineEdit()
        self.vnc_view_only_password.setEchoMode(QLineEdit.Password)
        self.vnc_view_only_password.setPlaceholderText("Nur-Ansicht Passwort (optional)")
        self.vnc_view_only_password.setText(self.settings.get("vnc", {}).get("view_only_password", ""))
        vnc_form.addRow("Nur-Ansicht Passwort:", self.vnc_view_only_password)
        
        vnc_info = QLabel(
            "⚠️ VNC ermöglicht Fernzugriff auf diesen Raspberry Pi. "
            "Die Einstellungen werden gespeichert, aber VNC muss manuell auf dem System konfiguriert werden."
        )
        vnc_info.setWordWrap(True)
        vnc_info.setStyleSheet(f"color: {self.theme_colors.text_secondary}; font-size: 11px;")
        vnc_form.addRow("", vnc_info)
        
        # VNC Control Buttons
        vnc_buttons = QHBoxLayout()
        
        self.vnc_start_btn = QPushButton("🟢 VNC Starten")
        self.vnc_start_btn.clicked.connect(lambda: self._control_vnc("start"))
        vnc_buttons.addWidget(self.vnc_start_btn)
        
        self.vnc_stop_btn = QPushButton("🔴 VNC Stoppen")
        self.vnc_stop_btn.clicked.connect(lambda: self._control_vnc("stop"))
        vnc_buttons.addWidget(self.vnc_stop_btn)
        
        self.vnc_status_btn = QPushButton("📊 Status")
        self.vnc_status_btn.clicked.connect(lambda: self._control_vnc("status"))
        vnc_buttons.addWidget(self.vnc_status_btn)
        
        vnc_form.addRow("", vnc_buttons)
        
        vnc_group.setLayout(vnc_form)
        layout.addWidget(vnc_group)
        
        self._on_vnc_enabled_changed(self.vnc_enabled.isChecked())
        
        layout.addStretch()
        return widget
    
    def _on_vnc_enabled_changed(self, enabled: bool):
        """Enable/disable VNC controls based on checkbox state."""
        self.vnc_password.setEnabled(enabled)
        self.vnc_view_only_password.setEnabled(enabled)
        self.vnc_start_btn.setEnabled(enabled)
        self.vnc_stop_btn.setEnabled(enabled)
    
    def _control_vnc(self, action: str):
        """Control VNC server (start/stop/status).
        
        Args:
            action: 'start', 'stop', or 'status'
        """
        import subprocess
        
        try:
            if action == "start":
                # Try to start VNC server
                result = subprocess.run(
                    ["sudo", "systemctl", "start", "vncserver-x11-serviced"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "VNC", "VNC Server wurde gestartet.")
                else:
                    QMessageBox.warning(
                        self, "VNC", 
                        f"Fehler beim Starten:\n{result.stderr or 'Unbekannter Fehler'}"
                    )
            
            elif action == "stop":
                # Try to stop VNC server
                result = subprocess.run(
                    ["sudo", "systemctl", "stop", "vncserver-x11-serviced"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "VNC", "VNC Server wurde gestoppt.")
                else:
                    QMessageBox.warning(
                        self, "VNC",
                        f"Fehler beim Stoppen:\n{result.stderr or 'Unbekannter Fehler'}"
                    )
            
            elif action == "status":
                # Check VNC status
                result = subprocess.run(
                    ["systemctl", "is-active", "vncserver-x11-serviced"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                status = result.stdout.strip()
                status_text = "🟢 Aktiv" if status == "active" else f"🔴 Inaktiv ({status})"
                
                # Try to get VNC connection info
                info_text = f"Status: {status_text}\n\n"
                try:
                    import socket
                    hostname = socket.gethostname()
                    ip = socket.gethostbyname(hostname)
                    info_text += f"Hostname: {hostname}\n"
                    info_text += f"IP-Adresse: {ip}\n"
                    info_text += f"VNC Port: 5900 (Standard)"
                except:
                    pass
                
                QMessageBox.information(self, "VNC Status", info_text)
        
        except subprocess.TimeoutExpired:
            QMessageBox.warning(self, "VNC", "Zeitüberschreitung beim Ausführen des Befehls.")
        except FileNotFoundError:
            QMessageBox.warning(
                self, "VNC", 
                "VNC-Tools nicht gefunden. Stelle sicher, dass RealVNC Server installiert ist."
            )
        except Exception as e:
            QMessageBox.warning(self, "VNC", f"Fehler: {str(e)}")

    def _create_about_tab(self) -> QWidget:
        """Create the about/settings credits tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        project_group = QGroupBox(t('settings.about_tab.project_group'))
        project_layout = QVBoxLayout()
        description = QLabel(t('settings.about_tab.project_description'))
        description.setWordWrap(True)
        project_layout.addWidget(description)
        
        repo_row = QHBoxLayout()
        repo_label = QLabel(t('settings.about_tab.repo_label'))
        repo_link = QLabel(f"<a href=\"{self.REPO_URL}\">{self.REPO_URL}</a>")
        repo_link.setTextFormat(Qt.RichText)
        repo_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        repo_link.setOpenExternalLinks(True)
        repo_row.addWidget(repo_label)
        repo_row.addWidget(repo_link, 1)
        project_layout.addLayout(repo_row)
        project_group.setLayout(project_layout)
        layout.addWidget(project_group)
        
        credits_group = QGroupBox(t('settings.about_tab.credits_group'))
        credits_layout = QVBoxLayout()
        weather_label = QLabel(
            t('settings.about_tab.credits_weather').format(
                provider=f"<a href=\"{self.WEATHER_PROVIDER_URL}\">Open-Meteo</a>"
            )
        )
        weather_label.setWordWrap(True)
        weather_label.setTextFormat(Qt.RichText)
        weather_label.setOpenExternalLinks(True)
        credits_layout.addWidget(weather_label)
        
        artwork_label = QLabel(
            t('settings.about_tab.credits_art').format(artist=self.ARTWORK_CREDIT)
        )
        artwork_label.setWordWrap(True)
        credits_layout.addWidget(artwork_label)
        
        license_label = QLabel(t('settings.about_tab.license_note'))
        license_label.setWordWrap(True)
        credits_layout.addWidget(license_label)
        
        credits_group.setLayout(credits_layout)
        layout.addWidget(credits_group)
        
        layout.addStretch()
        return widget
    
    def _create_daily_icons_tab(self) -> QWidget:
        """Create daily icons settings tab.
        
        Returns:
            Daily icons settings widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Mode Selection Group
        mode_group = QGroupBox("🎯 Tages-Icons Modus")
        mode_form = QFormLayout()
        
        self.daily_icons_mode = QComboBox()
        self.daily_icons_mode.addItem("🔁 Gleiche Icons jeden Tag", "always")
        self.daily_icons_mode.addItem("🗓️ Wochenplan", "weekly")
        self.daily_icons_mode.addItem("📌 Kalenderbasiert", "calendar")
        
        current_mode = self.settings.get("daily_icons", {}).get("mode", "always")
        mode_index = self.daily_icons_mode.findData(current_mode)
        if mode_index >= 0:
            self.daily_icons_mode.setCurrentIndex(mode_index)
        
        mode_form.addRow("Modus:", self.daily_icons_mode)
        mode_group.setLayout(mode_form)
        layout.addWidget(mode_group)
        
        # Default Icons Group (always mode)
        default_group = QGroupBox("🌟 Standard-Icons (täglich gleich)")
        default_layout = QVBoxLayout()
        
        default_icons = self.settings.get("daily_icons", {}).get("default_icons", ["🏰", "🌟", "🎨"])
        default_form = QFormLayout()
        
        self.default_icon_inputs = []
        for i in range(3):
            icon_input = QLineEdit()
            icon_input.setPlaceholderText("Emoji eingeben...")
            icon_input.setMaxLength(4)
            if i < len(default_icons):
                icon_input.setText(default_icons[i])
            default_form.addRow(f"Icon {i+1}:", icon_input)
            self.default_icon_inputs.append(icon_input)
        
        default_layout.addLayout(default_form)
        default_group.setLayout(default_layout)
        layout.addWidget(default_group)
        
        # Weekly Icons Group
        weekly_group = QGroupBox("📅 Wochenplan-Icons")
        weekly_layout = QVBoxLayout()
        
        weekly_hint = QLabel("Definiere für jeden Wochentag drei Icons:")
        weekly_hint.setWordWrap(True)
        weekly_layout.addWidget(weekly_hint)
        
        weekdays = [
            ("monday", "Montag"),
            ("tuesday", "Dienstag"),
            ("wednesday", "Mittwoch"),
            ("thursday", "Donnerstag"),
            ("friday", "Freitag"),
            ("saturday", "Samstag"),
            ("sunday", "Sonntag")
        ]
        
        self.weekly_icon_inputs = {}
        weekly_icons_config = self.settings.get("daily_icons", {}).get("weekly_icons", {})
        
        for day_key, day_label in weekdays:
            day_layout = QHBoxLayout()
            day_layout.addWidget(QLabel(f"{day_label}:"))
            
            day_inputs = []
            for i in range(3):
                icon_input = QLineEdit()
                icon_input.setPlaceholderText(f"Icon {i+1}")
                icon_input.setMaxLength(4)
                icon_input.setMaximumWidth(80)
                
                day_icons = weekly_icons_config.get(day_key, ["🏰", "🌟", "🎨"])
                if i < len(day_icons):
                    icon_input.setText(day_icons[i])
                
                day_layout.addWidget(icon_input)
                day_inputs.append(icon_input)
            
            self.weekly_icon_inputs[day_key] = day_inputs
            day_layout.addStretch()
            weekly_layout.addLayout(day_layout)
        
        weekly_group.setLayout(weekly_layout)
        layout.addWidget(weekly_group)
        
        # Calendar Mode Info
        calendar_group = QGroupBox("📌 Kalenderbasierter Modus")
        calendar_layout = QVBoxLayout()
        calendar_info = QLabel(
            "Im kalenderbasierten Modus werden die drei Icons automatisch aus den ersten drei Terminen des Tages geladen. "
            "Dies setzt voraus, dass die Kalender-Synchronisation aktiviert ist."
        )
        calendar_info.setWordWrap(True)
        calendar_layout.addWidget(calendar_info)
        calendar_group.setLayout(calendar_layout)
        layout.addWidget(calendar_group)
        
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
        self.font_size.valueChanged.connect(self._on_appearance_control_changed)
        font_form.addRow(t('settings.appearance_tab.font_size'), self.font_size)
        
        # Icon sizes for different elements
        self.tile_icon_size = QSpinBox()
        self.tile_icon_size.setMinimum(32)
        self.tile_icon_size.setMaximum(120)
        self.tile_icon_size.setValue(self.settings.get("appearance", {}).get("tile_icon_size", 64))
        self.tile_icon_size.valueChanged.connect(self._on_appearance_control_changed)
        font_form.addRow("Icon-Größe (Kacheln):", self.tile_icon_size)
        
        self.hero_icon_size = QSpinBox()
        self.hero_icon_size.setMinimum(64)
        self.hero_icon_size.setMaximum(160)
        self.hero_icon_size.setValue(self.settings.get("appearance", {}).get("hero_icon_size", 96))
        self.hero_icon_size.valueChanged.connect(self._on_appearance_control_changed)
        font_form.addRow("Icon-Größe (Tages-Icons):", self.hero_icon_size)
        
        self.calendar_icon_size = QSpinBox()
        self.calendar_icon_size.setMinimum(24)
        self.calendar_icon_size.setMaximum(96)
        self.calendar_icon_size.setValue(self.settings.get("appearance", {}).get("calendar_icon_size", 48))
        self.calendar_icon_size.valueChanged.connect(self._on_appearance_control_changed)
        font_form.addRow("Icon-Größe (Kalender):", self.calendar_icon_size)
        
        # Font scaling for smaller fonts
        self.font_scale_small = QSpinBox()
        self.font_scale_small.setMinimum(-50)
        self.font_scale_small.setMaximum(50)
        self.font_scale_small.setSuffix(" %")
        self.font_scale_small.setValue(self.settings.get("appearance", {}).get("font_scale_small", 0))
        self.font_scale_small.valueChanged.connect(self._on_appearance_control_changed)
        font_form.addRow(t('settings.appearance_tab.font_scale_small', default="Kleinere Fonts anpassen"), self.font_scale_small)
        
        # Font scaling for larger fonts
        self.font_scale_large = QSpinBox()
        self.font_scale_large.setMinimum(-50)
        self.font_scale_large.setMaximum(100)
        self.font_scale_large.setSuffix(" %")
        self.font_scale_large.setValue(self.settings.get("appearance", {}).get("font_scale_large", 50))
        self.font_scale_large.valueChanged.connect(self._on_appearance_control_changed)
        font_form.addRow(t('settings.appearance_tab.font_scale_large', default="Größere Fonts anpassen"), self.font_scale_large)
        
        # Font family
        self.font_family = QComboBox()
        self.font_family.addItems(["Arial", "Helvetica", "Verdana", "Tahoma", "Trebuchet MS", "Comic Sans MS"])
        current_font = self.settings.get("appearance", {}).get("font_family", "Arial")
        index = self.font_family.findText(current_font)
        if index >= 0:
            self.font_family.setCurrentIndex(index)
        self.font_family.currentTextChanged.connect(self._on_appearance_control_changed)
        font_form.addRow(t('settings.appearance_tab.font_family'), self.font_family)
        
        font_group.setLayout(font_form)
        layout.addWidget(font_group)
        
        # Theme settings
        theme_group = QGroupBox(t('settings.appearance_tab.theme_group'))
        theme_layout = QVBoxLayout()
        
        # Theme selection
        theme_select_layout = QHBoxLayout()
        
        self.theme_combo = QComboBox()
        self._populate_theme_list()
        
        current_theme = self.settings.get("appearance", {}).get("theme", "dark")
        theme_index = self.theme_combo.findData(current_theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        self.theme_combo.currentIndexChanged.connect(self._on_appearance_control_changed)
        
        theme_select_layout.addWidget(QLabel(t('settings.appearance_tab.theme')))
        theme_select_layout.addWidget(self.theme_combo, 1)
        theme_layout.addLayout(theme_select_layout)

        preview_row = QHBoxLayout()
        self.live_preview_checkbox = QCheckBox(t('settings.appearance_tab.live_preview'))
        self.live_preview_checkbox.setToolTip(t('settings.appearance_tab.live_preview_hint'))
        self.live_preview_checkbox.toggled.connect(self._on_live_preview_toggled)
        preview_row.addWidget(self.live_preview_checkbox)
        preview_row.addStretch()
        theme_layout.addLayout(preview_row)
        
        # Theme management buttons
        button_layout = QHBoxLayout()
        
        new_theme_btn = QPushButton("Neues Theme")
        new_theme_btn.clicked.connect(self._create_new_theme)
        button_layout.addWidget(new_theme_btn)
        
        edit_theme_btn = QPushButton("Bearbeiten")
        edit_theme_btn.clicked.connect(self._edit_current_theme)
        button_layout.addWidget(edit_theme_btn)
        
        delete_theme_btn = QPushButton("Löschen")
        delete_theme_btn.clicked.connect(self._delete_current_theme)
        button_layout.addWidget(delete_theme_btn)
        
        theme_layout.addLayout(button_layout)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        layout.addStretch()
        return widget

    def _on_live_preview_toggled(self, enabled: bool):
        """Handle live preview checkbox changes."""
        self.live_preview_enabled = enabled
        if enabled:
            self._emit_live_preview()
        else:
            self.theme_preview_reset.emit()
    
    def _on_appearance_control_changed(self, *args):
        """Forward control updates to preview when enabled."""
        if self.live_preview_checkbox and self.live_preview_checkbox.isChecked():
            self._emit_live_preview()
    
    def _emit_live_preview(self):
        """Emit a preview request with the current appearance values."""
        if not self.theme_combo:
            return
        theme_name = self.theme_combo.currentData()
        if not theme_name:
            return
        overrides = self._collect_preview_overrides()
        self.theme_preview_requested.emit(theme_name, overrides)
    
    def _collect_preview_overrides(self) -> dict:
        """Collect appearance overrides for theme preview."""
        return {
            "font_family": self.font_family.currentText(),
            "font_size": self.font_size.value(),
            "tile_icon_size": self.tile_icon_size.value(),
            "hero_icon_size": self.hero_icon_size.value(),
            "calendar_icon_size": self.calendar_icon_size.value(),
            "font_scale_small": self.font_scale_small.value(),
            "font_scale_large": self.font_scale_large.value()
        }
    
    def _create_tab_nav_button(self, symbol: str) -> QPushButton:
        """Create a large square navigation button for tab cycling."""
        btn = QPushButton(symbol)
        btn.setObjectName("TabNavButton")
        btn.setFixedSize(80, 80)
        return btn
    
    def _go_to_previous_tab(self):
        if not self.tabs:
            return
        index = max(0, self.tabs.currentIndex() - 1)
        self.tabs.setCurrentIndex(index)
    
    def _go_to_next_tab(self):
        if not self.tabs:
            return
        index = min(self.tabs.count() - 1, self.tabs.currentIndex() + 1)
        self.tabs.setCurrentIndex(index)
    
    def _update_tab_nav_buttons(self):
        if not self.tabs:
            return
        at_start = self.tabs.currentIndex() <= 0
        at_end = self.tabs.currentIndex() >= self.tabs.count() - 1
        if self.prev_tab_button:
            self.prev_tab_button.setEnabled(not at_start)
        if self.next_tab_button:
            self.next_tab_button.setEnabled(not at_end)
    
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
        
        # Update VNC settings
        if "vnc" not in self.settings:
            self.settings["vnc"] = {}
        self.settings["vnc"]["enabled"] = self.vnc_enabled.isChecked()
        self.settings["vnc"]["password"] = self.vnc_password.text()
        self.settings["vnc"]["view_only_password"] = self.vnc_view_only_password.text()
        
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
        self.settings["appearance"]["theme"] = self.theme_combo.currentData()
        self.settings["appearance"]["tile_icon_size"] = self.tile_icon_size.value()
        self.settings["appearance"]["hero_icon_size"] = self.hero_icon_size.value()
        self.settings["appearance"]["calendar_icon_size"] = self.calendar_icon_size.value()
        self.settings["appearance"]["font_scale_small"] = self.font_scale_small.value()
        self.settings["appearance"]["font_scale_large"] = self.font_scale_large.value()

        # Update daily_icons settings
        if "daily_icons" not in self.settings:
            self.settings["daily_icons"] = {}
        
        self.settings["daily_icons"]["mode"] = self.daily_icons_mode.currentData()
        
        # Save default icons
        default_icons = []
        for icon_input in self.default_icon_inputs:
            icon_text = icon_input.text().strip()
            if icon_text:
                default_icons.append(icon_text)
        if default_icons:
            self.settings["daily_icons"]["default_icons"] = default_icons
        
        # Save weekly icons
        weekly_icons = {}
        for day_key, day_inputs in self.weekly_icon_inputs.items():
            day_icons = []
            for icon_input in day_inputs:
                icon_text = icon_input.text().strip()
                if icon_text:
                    day_icons.append(icon_text)
            if day_icons:
                weekly_icons[day_key] = day_icons
        if weekly_icons:
            self.settings["daily_icons"]["weekly_icons"] = weekly_icons

        # Update launcher settings
        if "launcher" not in self.settings:
            self.settings["launcher"] = {}
        self.settings["launcher"]["grid_rows"] = self.launcher_grid_rows.value()
        self.settings["launcher"]["grid_columns"] = self.launcher_grid_columns.value()
        self.settings["launcher"]["apps"] = self.launcher_apps
        
        # Save to file
        self._save_settings()
        
        # Emit signal
        self.settings_changed.emit()
        
        # Request close
        self.close_requested.emit()
    
    def cancel(self):
        """Cancel settings - reset previews and close."""
        if self.live_preview_checkbox and self.live_preview_checkbox.isChecked():
            self.theme_preview_reset.emit()
        self.close_requested.emit()
    
    def _populate_theme_list(self):
        """Populate theme combo box with available themes."""
        self.theme_combo.clear()
        
        theme_manager = get_theme_manager()
        
        # Add preset themes
        preset_themes = theme_manager.get_preset_themes()
        for theme in preset_themes:
            self.theme_combo.addItem(f"📦 {theme.display_name}", theme.name)
        
        # Add separator if there are custom themes
        custom_themes = theme_manager.get_custom_themes()
        if custom_themes:
            self.theme_combo.insertSeparator(self.theme_combo.count())
            
            # Add custom themes
            for theme in custom_themes:
                self.theme_combo.addItem(f"✨ {theme.display_name}", theme.name)
    
    def _create_new_theme(self):
        """Create a new custom theme."""
        editor = ThemeEditorDialog(theme=None, parent=self)
        editor.theme_saved.connect(self._on_theme_saved)
        editor.exec_()
    
    def _edit_current_theme(self):
        """Edit the currently selected theme."""
        theme_name = self.theme_combo.currentData()
        if not theme_name:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie zuerst ein Theme aus!")
            return
        
        theme_manager = get_theme_manager()
        theme = theme_manager.get_theme(theme_name)
        
        if not theme:
            QMessageBox.warning(self, "Fehler", f"Theme '{theme_name}' nicht gefunden!")
            return
        
        # Can only edit custom themes
        if not theme.is_custom:
            QMessageBox.information(
                self,
                "Hinweis",
                "System-Themes können nicht bearbeitet werden.\n\n"
                "Sie können aber ein neues Theme erstellen, das auf diesem basiert."
            )
            return
        
        editor = ThemeEditorDialog(theme=theme, parent=self)
        editor.theme_saved.connect(self._on_theme_saved)
        editor.exec_()
    
    def _delete_current_theme(self):
        """Delete the currently selected theme."""
        theme_name = self.theme_combo.currentData()
        if not theme_name:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie zuerst ein Theme aus!")
            return
        
        theme_manager = get_theme_manager()
        theme = theme_manager.get_theme(theme_name)
        
        if not theme:
            QMessageBox.warning(self, "Fehler", f"Theme '{theme_name}' nicht gefunden!")
            return
        
        # Can only delete custom themes
        if not theme.is_custom:
            QMessageBox.warning(
                self,
                "Fehler",
                "System-Themes können nicht gelöscht werden!"
            )
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Theme löschen",
            f"Möchten Sie das Theme '{theme.display_name}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if theme_manager.delete_custom_theme(theme_name):
                QMessageBox.information(self, "Erfolg", "Theme wurde gelöscht!")
                
                # Refresh theme list
                current_theme = self.settings.get("appearance", {}).get("theme", "dark")
                self._populate_theme_list()
                
                # If deleted theme was selected, switch to dark
                if current_theme == theme_name:
                    self.theme_combo.setCurrentIndex(0)  # Select first theme
                else:
                    theme_index = self.theme_combo.findData(current_theme)
                    if theme_index >= 0:
                        self.theme_combo.setCurrentIndex(theme_index)
            else:
                QMessageBox.warning(self, "Fehler", "Theme konnte nicht gelöscht werden!")
    
    def _on_theme_saved(self, theme):
        """Handle theme saved from editor.
        
        Args:
            theme: Saved theme
        """
        theme_manager = get_theme_manager()
        
        # Save theme
        if theme_manager.save_custom_theme(theme):
            QMessageBox.information(self, "Erfolg", f"Theme '{theme.display_name}' wurde gespeichert!")
            
            # Refresh theme list
            self._populate_theme_list()
            
            # Select the newly saved theme
            theme_index = self.theme_combo.findData(theme.name)
            if theme_index >= 0:
                self.theme_combo.setCurrentIndex(theme_index)
        else:
            QMessageBox.warning(self, "Fehler", "Theme konnte nicht gespeichert werden!")


class AppConfigDialog(QDialog):
    """Dialog for configuring individual launcher apps."""

    def __init__(self, parent=None, app_data: Optional[dict] = None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(
            t('settings.apps_tab.dialog_title_edit') if app_data else t('settings.apps_tab.dialog_title_new')
        )
        self.app_data = app_data.copy() if app_data else {}
        self._init_ui()
        if app_data:
            self._load_data(app_data)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(t('settings.apps_tab.name_placeholder'))
        form.addRow(t('settings.apps_tab.name'), self.name_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(t('settings.apps_tab.types.python'), "python")
        self.type_combo.addItem(t('settings.apps_tab.types.website'), "website")
        self.type_combo.currentIndexChanged.connect(self._update_type_fields)
        form.addRow(t('settings.apps_tab.type'), self.type_combo)
        
        # Python app fields
        python_row = QHBoxLayout()
        self.python_path_input = QLineEdit()
        python_row.addWidget(self.python_path_input, 1)
        browse_python = QPushButton(t('common.browse'))
        browse_python.clicked.connect(self._browse_python_file)
        python_row.addWidget(browse_python)
        python_container = QWidget()
        python_container.setLayout(python_row)
        form.addRow(t('settings.apps_tab.python_path'), python_container)
        self.python_row_widget = python_container
        
        # Website fields
        self.website_url_input = QLineEdit()
        self.website_url_input.setPlaceholderText("https://example.com")
        form.addRow(t('settings.apps_tab.website_url'), self.website_url_input)
        self.website_row_widget = self.website_url_input
        
        layout.addLayout(form)
        
        button_row = QHBoxLayout()
        save_btn = QPushButton(t('common.save'))
        save_btn.clicked.connect(self._on_accept)
        button_row.addWidget(save_btn)
        cancel_btn = QPushButton(t('common.cancel'))
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(cancel_btn)
        button_row.addStretch()
        layout.addLayout(button_row)
        
        self._update_type_fields()

    def _load_data(self, data: dict):
        self.name_input.setText(data.get("name", ""))
        type_value = data.get("type", "python")
        idx = self.type_combo.findData(type_value)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        value = data.get("value", "")
        if type_value == "python":
            self.python_path_input.setText(value)
        else:
            self.website_url_input.setText(value)

    def _update_type_fields(self):
        current_type = self.type_combo.currentData()
        is_python = current_type == "python"
        self.python_row_widget.setVisible(is_python)
        self.website_row_widget.setVisible(not is_python)

    def _browse_python_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            t('settings.apps_tab.choose_python'),
            str(Path.home()),
            "Python (*.py)"
        )
        if path:
            self.python_path_input.setText(path)

    def _on_accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, t('common.error'), t('settings.apps_tab.validation_name'))
            return
        app_type = self.type_combo.currentData()
        if app_type == "python":
            value = self.python_path_input.text().strip()
            if not value:
                QMessageBox.warning(self, t('common.error'), t('settings.apps_tab.validation_python'))
                return
        else:
            value = self.website_url_input.text().strip()
            if not value:
                QMessageBox.warning(self, t('common.error'), t('settings.apps_tab.validation_website'))
                return
        self.app_data = {
            "name": name,
            "type": app_type,
            "value": value
        }
        self.accept()  # This is still a QDialog, keep accept()
