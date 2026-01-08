"""
Dashboard View - Main launcher screen with app tiles.

Shows tiles for:
- Calendar (weather + today's icons)
- Chromium apps (anton.app, etc.)
- Other apps (to be added)
"""

from datetime import date
from pathlib import Path
from typing import Callable, Dict, Optional
import subprocess

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

from utils.i18n import t
from themes.theme_manager import Theme, ThemeColors, ThemeDecoration


class AppTile(QFrame):
    """Single app tile widget."""
    
    clicked = pyqtSignal()
    
    def __init__(self, icon: str, title: str, subtitle: str = "", parent=None, theme_colors: Optional[ThemeColors] = None):
        """Initialize app tile.
        
        Args:
            icon: Emoji or icon string
            title: App title
            subtitle: Optional subtitle text
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setObjectName("AppTile")
        self.theme_colors = theme_colors or ThemeColors()
        self.setCursor(Qt.PointingHandCursor)
        self.icon_font_size = 68
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        self._layout = layout
        
        # Icon
        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFont(QFont("Comic Sans MS", self.icon_font_size))
        self.icon_label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Comic Sans MS", 18, QFont.Bold))  # Will be updated by theme
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Subtitle (optional)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setAlignment(Qt.AlignCenter)
            subtitle_label.setFont(QFont("Comic Sans MS", 13))  # Will be updated by theme
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)
        else:
            subtitle_label = None
        
        self.icon_label = self.icon_label  # Already set above
        self.title_label = title_label
        self.subtitle_label = subtitle_label
        self._apply_styles()

    def set_icon_text(self, icon_text: str):
        """Dynamically change the tile icon label."""
        if self.icon_label is not None:
            self.icon_label.setText(icon_text or "")

    def set_title_text(self, title_text: str):
        """Dynamically change the tile title."""
        if self.title_label is not None:
            self.title_label.setText(title_text or "")

    def set_subtitle_text(self, subtitle_text: Optional[str]):
        """Ensure subtitle label exists and update its contents."""
        if subtitle_text and not self.subtitle_label:
            subtitle_label = QLabel(subtitle_text)
            subtitle_label.setAlignment(Qt.AlignCenter)
            subtitle_label.setFont(QFont("Comic Sans MS", 13))
            subtitle_label.setWordWrap(True)
            self._layout.addWidget(subtitle_label)
            self.subtitle_label = subtitle_label
            self._apply_styles()
        if self.subtitle_label:
            self.subtitle_label.setText(subtitle_text or "")
            self.subtitle_label.setVisible(bool(subtitle_text))
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def apply_colors(self, colors: ThemeColors):
        """Update tile colors."""
        self.theme_colors = colors
        self._apply_styles()

    def _apply_styles(self):
        """Apply stylesheet based on current colors."""
        c = self.theme_colors
        self.setStyleSheet(f"""
            AppTile {{
                background-color: {c.background_secondary};
                border: 3px solid {c.border};
                border-radius: 28px;
                padding: 26px;
            }}
            AppTile:hover {{
                background-color: {c.background_hover};
                border-color: {c.accent_light};
            }}
            AppTile:disabled {{
                background-color: {c.background};
                border-style: dashed;
                color: {c.text_disabled};
            }}
        """)
        if self.title_label:
            self.title_label.setStyleSheet(f"color: {c.text_primary};")
        if self.subtitle_label:
            self.subtitle_label.setStyleSheet(f"color: {c.text_secondary};")

    def set_icon_size(self, size: int):
        """Adjust tile icon size based on appearance settings."""
        try:
            sanitized = int(size)
        except (TypeError, ValueError):
            sanitized = self.icon_font_size
        sanitized = max(32, min(128, sanitized))
        self.icon_font_size = sanitized
        if hasattr(self, 'icon_label'):
            font = self.icon_label.font()
            font.setPointSize(sanitized)
            self.icon_label.setFont(font)


class DashboardView(QWidget):
    """Dashboard view showing app launcher tiles."""
    
    calendar_clicked = pyqtSignal()
    
    def __init__(self, database, parent=None, scale_factor: float = 1.0):
        """Initialize dashboard view.
        
        Args:
            database: CalendarDatabase instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.layout_scale = max(0.5, min(scale_factor, 1.0))
        self.database = database
        self.current_date = date.today()
        self.settings_path = Path(__file__).resolve().parent.parent / "config" / "settings.json"
        self.launcher_config = self._load_launcher_config()
        self.artwork_root = Path(__file__).resolve().parent.parent / "resources" / "artwork"
        self.default_artwork_pack = "mochi_024"
        self.default_artwork = {
            "background": f"{self.default_artwork_pack}/princess-9754251_640.png",
            "hero_left": f"{self.default_artwork_pack}/girl_knight.png",
            "hero_right": f"{self.default_artwork_pack}/unicorn_pink.png",
            "stickers": [
                f"{self.default_artwork_pack}/crown.png",
                f"{self.default_artwork_pack}/wand.png",
                f"{self.default_artwork_pack}/frog.png"
            ]
        }
        self.artwork_labels: Dict[str, Dict[str, object]] = {}
        self.theme_colors = ThemeColors()
        self.icon_font_size = 96  # Larger icons for hero display
        
        self._init_ui()
        self.set_layout_scale(self.layout_scale)
        self.refresh()
    
    def _load_launcher_config(self) -> dict:
        """Load launcher configuration from settings.json.
        
        Returns:
            Launcher config dict with grid and apps
        """
        import json
        default_config = {
            "grid_rows": 2,
            "grid_columns": 2,
            "apps": []
        }
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r') as f:
                    settings = json.load(f)
                    config = settings.get("launcher", default_config)
                    
                    # Dynamically add Anton app if enabled
                    anton_settings = settings.get("anton", {})
                    if anton_settings.get("enabled", True):
                        anton_app = self._create_anton_app_config(anton_settings)
                        # Check if Anton is already in apps list
                        if not any(app.get("id") == "anton" for app in config.get("apps", [])):
                            config.setdefault("apps", []).insert(0, anton_app)
                    else:
                        # Remove Anton if disabled
                        config["apps"] = [app for app in config.get("apps", []) if app.get("id") != "anton"]
                    
                    return config
        except Exception as e:
            print(f"Error loading launcher config: {e}")
        return default_config
    
    def _create_anton_app_config(self, anton_settings: dict) -> dict:
        """Create Anton app configuration from settings.
        
        Args:
            anton_settings: Anton settings from config
            
        Returns:
            App config dict for Anton
        """
        auto_login = anton_settings.get("auto_login", True)
        login_method = anton_settings.get("login_method", "code")
        
        # Build URL with login code if auto-login enabled and method is code
        url = "https://anton.app"
        if auto_login and login_method == "code":
            login_code = anton_settings.get("login_code", "").strip()
            if login_code:
                url = f"https://anton.app/code/{login_code}"
        # For email/phone, just open Anton - user needs to login manually
        
        # Build chromium command
        command = f'chromium --kiosk --noerrdialogs --disable-infobars --no-first-run "{url}"'
        
        return {
            "id": "anton",
            "type": "website",
            "name": "Anton",
            "subtitle": "Lernen",
            "icon": "🎓",
            "command": command,
            "url": url,
            "kiosk": True
        }
    
    def _init_ui(self):
        """Initialize the user interface."""
        self.setObjectName("DashboardView")
        self._apply_background_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 40)
        layout.setSpacing(24)
        
        # Header with artwork, date and today's icons
        header_layout = QVBoxLayout()
        header_layout.setSpacing(16)
        
        self.icons_layout = QHBoxLayout()
        self.icons_layout.setSpacing(24)
        self.icons_layout.setAlignment(Qt.AlignCenter)
        
        self.icon_labels = []
        for _ in range(3):
            icon_label = QLabel("🏰")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFont(QFont("Comic Sans MS", self.icon_font_size))
            icon_label.setStyleSheet("border: none; background: transparent;")
            self.icons_layout.addWidget(icon_label)
            self.icon_labels.append(icon_label)
        
        icons_container = QWidget()
        icons_container.setLayout(self.icons_layout)
        
        hero_layout = QHBoxLayout()
        hero_layout.setSpacing(12)
        hero_layout.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(
            self._create_registered_artwork_label("hero_left", self.default_artwork["hero_left"], 190),
            0,
            Qt.AlignBottom
        )
        hero_layout.addWidget(icons_container, 1)
        hero_layout.addWidget(
            self._create_registered_artwork_label("hero_right", self.default_artwork["hero_right"], 190),
            0,
            Qt.AlignBottom
        )
        header_layout.addLayout(hero_layout)
        
        self.date_label = QLabel()
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setFont(QFont("Comic Sans MS", 18, QFont.Bold))
        self.date_label.setStyleSheet("color: #9B5C8B; background: transparent;")
        header_layout.addWidget(self.date_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # App tiles grid - dynamically built from launcher config
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        self.app_tiles = []
        self._build_app_grid()
        
        layout.addLayout(self.grid, 1)
        layout.addLayout(self._create_sticker_row())
    
        self.apply_theme(None)

    def set_layout_scale(self, scale_factor: float):
        """Resize paddings and artwork to fit small displays."""
        self.layout_scale = max(0.5, min(scale_factor, 1.0))
        root_layout = self.layout()
        if root_layout:
            margin = int(30 * self.layout_scale)
            root_layout.setContentsMargins(margin, margin, margin, int(40 * self.layout_scale))
            root_layout.setSpacing(int(24 * self.layout_scale))
        if hasattr(self, 'icons_layout'):
            self.icons_layout.setSpacing(int(24 * self.layout_scale))
        if hasattr(self, 'grid'):
            self.grid.setSpacing(int(20 * self.layout_scale))
        for config in self.artwork_labels.values():
            base_size = config.get("base_size", config.get("max_size", 190))
            config["max_size"] = max(60, int(base_size * self.layout_scale))
            role = config.get("role")
            asset = config.get("current_asset") or config.get("fallback")
            if role:
                self._set_label_artwork(role, asset)
        self._update_today_icons()

    def _build_app_grid(self):
        """Build the app grid dynamically from launcher config."""
        # Clear existing tiles
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.app_tiles.clear()
        
        rows = self.launcher_config.get("grid_rows", 2)
        cols = self.launcher_config.get("grid_columns", 2)
        apps = self.launcher_config.get("apps", [])
        
        # Always add calendar tile first
        self.calendar_tile = self._create_calendar_tile()
        self.grid.addWidget(self.calendar_tile, 0, 0)
        self.app_tiles.append(self.calendar_tile)
        
        # Add configured launcher apps
        for idx, app_config in enumerate(apps):
            # Calculate position (skip 0,0 which is calendar)
            position = idx + 1
            row = position // cols
            col = position % cols
            
            # Don't exceed grid bounds
            if row >= rows:
                break
            
            tile = self._create_app_tile_from_config(app_config)
            self.grid.addWidget(tile, row, col)
            self.app_tiles.append(tile)
        
        # Fill remaining slots with empty tiles if needed
        total_slots = rows * cols
        for position in range(len(self.app_tiles), total_slots):
            row = position // cols
            col = position % cols
            placeholder = AppTile("📦", "Leer", "Nicht konfiguriert", theme_colors=self.theme_colors)
            placeholder.setEnabled(False)
            self.grid.addWidget(placeholder, row, col)
            self.app_tiles.append(placeholder)
    
    def _create_app_tile_from_config(self, config: dict) -> AppTile:
        """Create an app tile from launcher configuration.
        
        Args:
            config: App config dict with id, name, icon, command
            
        Returns:
            Configured AppTile
        """
        icon = config.get("icon", "📱")
        name = config.get("name", "App")
        subtitle = config.get("subtitle", "")
        command = config.get("command", "")
        
        tile = AppTile(icon, name, subtitle, theme_colors=self.theme_colors)
        
        # Connect click to launch command
        if command:
            tile.clicked.connect(lambda: self._launch_command(command))
        else:
            tile.setEnabled(False)
        
        return tile
    
    def _launch_command(self, command: str):
        """Launch external command.
        
        Args:
            command: Command string to execute
        """
        print(f"Launching: {command}")
        try:
            subprocess.Popen(command, shell=True)
        except Exception as e:
            print(f"Error launching command: {e}")

    def _create_calendar_tile(self) -> AppTile:
        """Create calendar tile with dynamic content.
        
        Returns:
            Calendar app tile
        """
        tile = AppTile("📅", "Kalender", "Heute", theme_colors=self.theme_colors)
        tile.clicked.connect(self.calendar_clicked.emit)
        
        # Store reference to update content
        self.calendar_tile_widget = tile
        
        return tile

    def _create_sticker_row(self) -> QHBoxLayout:
        """Create a decorative row of sticker icons using artwork assets."""
        sticker_layout = QHBoxLayout()
        sticker_layout.setSpacing(24)
        sticker_layout.setAlignment(Qt.AlignCenter)
        for idx, filename in enumerate(self.default_artwork["stickers"]):
            role = f"sticker_{idx}"
            sticker_layout.addWidget(self._create_registered_artwork_label(role, filename, 96))
        return sticker_layout

    def _create_registered_artwork_label(self, role: str, fallback_asset: str, max_size: int = 210) -> QLabel:
        """Create and register an artwork label so it can be themed later."""
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background: transparent; border: none;")
        self.artwork_labels[role] = {
            "role": role,
            "label": label,
            "fallback": fallback_asset,
            "max_size": max_size,
            "base_size": max_size,
            "current_asset": fallback_asset
        }
        self._set_label_artwork(role, fallback_asset)
        return label

    def _set_label_artwork(self, role: str, asset_path: Optional[str]):
        """Update a registered artwork label with the requested asset."""
        config = self.artwork_labels.get(role)
        if not config:
            return
        label: QLabel = config["label"]
        max_size = int(config["max_size"])
        fallback = config["fallback"]
        candidate = asset_path or fallback
        pixmap = None
        resolved = self._resolve_artwork_path(candidate)
        if resolved:
            pixmap = QPixmap(str(resolved))
        if pixmap and not pixmap.isNull():
            label.setPixmap(pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setText("")
        else:
            label.setPixmap(QPixmap())
            label.setText("✨")
            label.setFont(QFont("Comic Sans MS", max(24, int(max_size * 0.35))))
        config["current_asset"] = candidate

    def _resolve_artwork_path(self, relative_or_absolute: Optional[str]) -> Optional[Path]:
        """Resolve artwork path regardless of whether it is absolute or relative."""
        if not relative_or_absolute:
            return None
        candidate = Path(relative_or_absolute)
        if not candidate.is_absolute():
            candidate = self.artwork_root / relative_or_absolute
        return candidate if candidate.exists() else None

    def _update_artwork_decorations(self, decoration: Optional[ThemeDecoration]):
        """Update hero, sticker, and background artwork selections."""
        decoration = decoration or ThemeDecoration()
        self._set_label_artwork("hero_left", decoration.hero_left_image)
        self._set_label_artwork("hero_right", decoration.hero_right_image)
        stickers = decoration.sticker_images or []
        for idx, fallback in enumerate(self.default_artwork["stickers"]):
            asset = stickers[idx] if idx < len(stickers) else None
            role = f"sticker_{idx}"
            # Use custom asset if provided, otherwise fall back to defaults
            self._set_label_artwork(role, asset or fallback)

    def _apply_background_style(self, decoration: Optional[ThemeDecoration] = None):
        """Apply a themed background image if configured."""
        base_color = self.theme_colors.background
        background_asset = self.default_artwork["background"]
        if decoration and decoration.background_pattern:
            background_asset = decoration.background_pattern
        background_path = self._resolve_artwork_path(background_asset)
        background_rule = ""
        if background_path:
            background_rule = (
                f"background-image: url('{background_path.as_posix()}');"
                "background-position: top center;"
                "background-repeat: no-repeat;"
            )
        self.setStyleSheet(f"""
            QWidget#DashboardView {{
                background-color: {base_color};
                {background_rule}
            }}
            QLabel#DateLabel {{
                color: {self.theme_colors.text_secondary};
            }}
        """)

    def apply_theme(self, theme: Optional[Theme]):
        """Apply the active theme to dashboard widgets."""
        self.theme_colors = theme.colors if theme else ThemeColors()
        decoration = theme.decoration if theme else None
        self._apply_background_style(decoration)
        self._update_artwork_decorations(decoration)
        # Update date label font from theme
        if theme and hasattr(theme, 'font'):
            self.date_label.setFont(QFont(theme.font.family, theme.font.size_large, QFont.Bold))
        self.date_label.setStyleSheet(f"color: {self.theme_colors.text_secondary}; background: transparent;")
        for tile in getattr(self, 'app_tiles', []):
            tile.apply_colors(self.theme_colors)

    def set_tile_icon_size(self, size: int):
        """Resize app tile icons based on appearance settings."""
        try:
            sanitized = int(size)
        except (TypeError, ValueError):
            sanitized = 64
        sanitized = max(32, min(120, sanitized))
        for tile in getattr(self, 'app_tiles', []):
            if hasattr(tile, 'set_icon_size'):
                tile.set_icon_size(sanitized)
    
    def set_hero_icon_size(self, size: int):
        """Resize the top hero icons (daily icons) based on appearance settings."""
        try:
            sanitized = int(size)
        except (TypeError, ValueError):
            sanitized = self.icon_font_size
        sanitized = max(64, min(160, sanitized))
        self.icon_font_size = sanitized
        for label in getattr(self, 'icon_labels', []):
            font = label.font()
            font.setPointSize(sanitized)
            label.setFont(font)

    def set_icon_size(self, size: int):
        """Legacy method - delegates to set_tile_icon_size for compatibility."""
        self.set_tile_icon_size(size)    
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
        """Update today's icon display based on configured mode."""
        import json
        
        # Load daily_icons settings
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r') as f:
                    settings = json.load(f)
                    daily_icons_config = settings.get("daily_icons", {})
            else:
                daily_icons_config = {}
        except Exception:
            daily_icons_config = {}
        
        mode = daily_icons_config.get("mode", "always")
        icons_to_display = ["🏰", "🌟", "🎨"]  # Defaults
        
        if mode == "always":
            # Use default icons
            icons_to_display = daily_icons_config.get("default_icons", icons_to_display)
        elif mode == "weekly":
            # Use weekday-specific icons
            weekday_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            weekday = weekday_keys[self.current_date.weekday()]
            weekly_icons = daily_icons_config.get("weekly_icons", {})
            icons_to_display = weekly_icons.get(weekday, icons_to_display)
        elif mode == "calendar":
            # Use calendar entries (top 3 by category)
            entries = self.database.get_entries_by_date(self.current_date)
            icons_to_display = []
            for i in range(min(3, len(entries))):
                entry = entries[i]
                icon_emoji = self._get_icon_emoji(entry['category'])
                icons_to_display.append(icon_emoji)
            # Fill remaining slots with home icon
            while len(icons_to_display) < 3:
                icons_to_display.append("🏠")
        
        # Update the three icon labels
        for i in range(3):
            if i < len(icons_to_display):
                self.icon_labels[i].setText(icons_to_display[i])
                self.icon_labels[i].setVisible(True)
            else:
                self.icon_labels[i].setText("🏠")
                self.icon_labels[i].setVisible(True)
    
    def _update_calendar_tile(self):
        """Update calendar tile with today's weather and events."""
        # Get today's entries
        entries = self.database.get_entries_by_date(self.current_date)
        weather = self.database.get_weather(self.current_date)
        
        # Build subtitle with weather and event count
        subtitle_parts = []
        icon_text = "📅"
        if weather:
            weather_icon = self._get_weather_emoji(weather.get('description', 'clear'))
            temps = []
            if weather.get('temperature_high') is not None and weather.get('temperature_low') is not None:
                temps.append(f"{int(weather['temperature_high'])}°/{int(weather['temperature_low'])}°")
            elif weather.get('temperature_high') is not None:
                temps.append(f"{int(weather['temperature_high'])}°")
            description = weather.get('description')
            parts = " ".join(filter(None, [" ".join(temps).strip(), description])).strip()
            subtitle_parts.append(f"{weather_icon} {parts}".strip())
            icon_text = weather_icon
        
        if entries:
            event_count = len(entries)
            subtitle_parts.append(f"{event_count} Termine")
        else:
            subtitle_parts.append("Keine Termine")
        
        subtitle = " • ".join(filter(None, subtitle_parts))
        if hasattr(self, 'calendar_tile_widget'):
            self.calendar_tile_widget.set_icon_text(icon_text)
            self.calendar_tile_widget.set_subtitle_text(subtitle)
    
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
