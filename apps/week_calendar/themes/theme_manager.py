"""
Theme Management System

Handles loading, saving, and applying themes with colors, fonts, and decorations.
Supports custom user themes and preset themes.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class ThemeColors:
    """Color definitions for a theme."""
    
    # Background colors
    background: str = "#2C3E50"
    background_secondary: str = "#34495E"
    background_hover: str = "#3D5A6C"
    
    # Text colors
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#BDC3C7"
    text_disabled: str = "#7F8C8D"
    
    # Accent colors
    accent: str = "#1ABC9C"
    accent_hover: str = "#16A085"
    accent_light: str = "#48C9B0"
    
    # Status colors
    success: str = "#27AE60"
    warning: str = "#F39C12"
    error: str = "#E74C3C"
    info: str = "#3498DB"
    
    # UI element colors
    border: str = "#34495E"
    shadow: str = "rgba(0, 0, 0, 0.2)"
    
    # Calendar specific
    today_highlight: str = "#1ABC9C"
    weekend: str = "#5D6D7E"
    event_default: str = "#3498DB"


@dataclass
class ThemeFont:
    """Font definitions for a theme."""
    
    family: str = "Arial"
    size_small: int = 10
    size_normal: int = 12
    size_large: int = 14
    size_xlarge: int = 16
    size_heading: int = 18
    size_title: int = 20
    weight_normal: str = "normal"
    weight_bold: str = "bold"


@dataclass
class ThemeDecoration:
    """Decoration settings for a theme (icons, patterns, etc.)."""
    
    # Decoration theme (dinosaurs, princess, football, horses, etc.)
    style: str = "none"  # none, dinosaurs, princess, football, horses, space, ocean
    
    # Icon set
    icon_style: str = "default"  # default, rounded, flat, outline
    
    # Optional background pattern/image
    background_pattern: Optional[str] = None  # Path to pattern image
    
    # Corner decorations (small icons in corners)
    corner_decoration: bool = False
    corner_icon: Optional[str] = None  # Path to corner icon
    
    # Border decorations
    border_style: str = "solid"  # solid, dashed, decorated
    border_decoration: Optional[str] = None  # Path to border decoration image
    hero_left_image: Optional[str] = None  # Path to left hero artwork
    hero_right_image: Optional[str] = None  # Path to right hero artwork
    sticker_images: List[str] = field(default_factory=list)  # Decorative stickers


@dataclass
class Theme:
    """Complete theme definition."""
    
    # Metadata
    name: str = "Default"
    display_name: str = "Default Theme"
    description: str = "Default theme"
    author: str = "System"
    is_custom: bool = False
    
    # Theme components
    colors: ThemeColors = None
    font: ThemeFont = None
    decoration: ThemeDecoration = None
    
    def __post_init__(self):
        """Initialize sub-components if not provided."""
        if self.colors is None:
            self.colors = ThemeColors()
        if self.font is None:
            self.font = ThemeFont()
        if self.decoration is None:
            self.decoration = ThemeDecoration()
    
    def to_dict(self) -> dict:
        """Convert theme to dictionary.
        
        Returns:
            Theme as dictionary
        """
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "author": self.author,
            "is_custom": self.is_custom,
            "colors": asdict(self.colors),
            "font": asdict(self.font),
            "decoration": asdict(self.decoration)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Theme':
        """Create theme from dictionary.
        
        Args:
            data: Theme data dictionary
            
        Returns:
            Theme instance
        """
        colors_data = data.get("colors", {})
        font_data = data.get("font", {})
        decoration_data = data.get("decoration", {})
        
        return cls(
            name=data.get("name", "default"),
            display_name=data.get("display_name", "Default"),
            description=data.get("description", ""),
            author=data.get("author", "System"),
            is_custom=data.get("is_custom", False),
            colors=ThemeColors(**colors_data),
            font=ThemeFont(**font_data),
            decoration=ThemeDecoration(**decoration_data)
        )
    
    def generate_stylesheet(self) -> str:
        """Generate PyQt5 stylesheet from theme.
        
        Returns:
            Complete stylesheet string
        """
        c = self.colors
        f = self.font
        
        stylesheet = f"""
            /* Main Window */
            QMainWindow {{
                background-color: {c.background};
                color: {c.text_primary};
                font-family: {f.family};
                font-size: {f.size_normal}px;
            }}
            
            /* Generic Widget */
            QWidget {{
                background-color: {c.background};
                color: {c.text_primary};
                font-family: {f.family};
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 8px;
                padding: 10px;
                font-size: {f.size_normal}px;
                font-weight: {f.weight_bold};
            }}
            
            QPushButton:hover {{
                background-color: {c.background_hover};
            }}
            
            QPushButton:pressed {{
                background-color: {c.accent};
            }}
            
            QPushButton:disabled {{
                background-color: {c.background_secondary};
                color: {c.text_disabled};
            }}
            
            /* Labels */
            QLabel {{
                color: {c.text_primary};
                background-color: transparent;
                font-size: {f.size_normal}px;
            }}
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 4px;
                padding: 5px;
                font-size: {f.size_normal}px;
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {c.accent};
            }}
            
            /* Combo Boxes */
            QComboBox {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 4px;
                padding: 5px;
                font-size: {f.size_normal}px;
            }}
            
            QComboBox:hover {{
                background-color: {c.background_hover};
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                selection-background-color: {c.accent};
                border: 1px solid {c.border};
            }}
            
            /* Check Boxes */
            QCheckBox {{
                color: {c.text_primary};
                spacing: 8px;
                font-size: {f.size_normal}px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {c.border};
                border-radius: 3px;
                background-color: {c.background_secondary};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {c.accent};
                border-color: {c.accent};
            }}
            
            /* Spin Boxes */
            QSpinBox, QDoubleSpinBox {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 4px;
                padding: 5px;
                font-size: {f.size_normal}px;
            }}
            
            /* Group Boxes */
            QGroupBox {{
                color: {c.text_primary};
                border: 2px solid {c.border};
                border-radius: 8px;
                margin-top: 10px;
                font-size: {f.size_normal}px;
                font-weight: {f.weight_bold};
                padding-top: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {c.accent};
            }}
            
            /* List Widgets */
            QListWidget {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 4px;
                font-size: {f.size_normal}px;
            }}
            
            QListWidget::item:selected {{
                background-color: {c.accent};
                color: {c.text_primary};
            }}
            
            QListWidget::item:hover {{
                background-color: {c.background_hover};
            }}
            
            /* Tab Widget */
            QTabWidget::pane {{
                border: 1px solid {c.border};
                border-radius: 4px;
                background-color: {c.background};
            }}
            
            QTabBar::tab {{
                background-color: {c.background_secondary};
                color: {c.text_secondary};
                border: 1px solid {c.border};
                padding: 8px 16px;
                font-size: {f.size_normal}px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {c.accent};
                color: {c.text_primary};
            }}
            
            QTabBar::tab:hover {{
                background-color: {c.background_hover};
            }}
            
            /* Scroll Bars */
            QScrollBar:vertical {{
                background-color: {c.background_secondary};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {c.accent};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {c.accent_hover};
            }}
            
            QScrollBar:horizontal {{
                background-color: {c.background_secondary};
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {c.accent};
                border-radius: 6px;
                min-width: 20px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {c.accent_hover};
            }}
            
            QScrollBar::add-line, QScrollBar::sub-line {{
                height: 0px;
                width: 0px;
            }}
            
            /* Dialogs */
            QDialog {{
                background-color: {c.background};
                color: {c.text_primary};
            }}
            
            /* Message Box */
            QMessageBox {{
                background-color: {c.background};
                color: {c.text_primary};
            }}
            
            QMessageBox QPushButton {{
                min-width: 80px;
            }}
            
            /* Tool Tip */
            QToolTip {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 4px;
                padding: 5px;
                font-size: {f.size_small}px;
            }}
        """
        
        return stylesheet


class ThemeManager:
    """Manages themes - loading, saving, applying."""
    
    def __init__(self):
        """Initialize theme manager."""
        self.themes_dir = Path(__file__).parent / "presets"
        self.custom_themes_dir = Path(__file__).parent.parent / "config" / "custom_themes"
        
        # Create directories if they don't exist
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.custom_themes_dir.mkdir(parents=True, exist_ok=True)
        
        self._themes: Dict[str, Theme] = {}
        self._load_all_themes()
    
    def _load_all_themes(self):
        """Load all themes from preset and custom directories."""
        # Load preset themes
        for theme_file in self.themes_dir.glob("*.json"):
            try:
                theme = self._load_theme_file(theme_file)
                if theme:
                    theme.is_custom = False
                    self._themes[theme.name] = theme
            except Exception as e:
                print(f"Error loading preset theme {theme_file}: {e}")
        
        # Load custom themes
        for theme_file in self.custom_themes_dir.glob("*.json"):
            try:
                theme = self._load_theme_file(theme_file)
                if theme:
                    theme.is_custom = True
                    self._themes[theme.name] = theme
            except Exception as e:
                print(f"Error loading custom theme {theme_file}: {e}")
    
    def _load_theme_file(self, path: Path) -> Optional[Theme]:
        """Load theme from JSON file.
        
        Args:
            path: Path to theme JSON file
            
        Returns:
            Theme instance or None if loading failed
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Theme.from_dict(data)
        except Exception as e:
            print(f"Error loading theme from {path}: {e}")
            return None
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """Get theme by name.
        
        Args:
            name: Theme name
            
        Returns:
            Theme instance or None if not found
        """
        return self._themes.get(name)
    
    def get_all_themes(self) -> List[Theme]:
        """Get list of all available themes.
        
        Returns:
            List of all themes
        """
        return list(self._themes.values())
    
    def get_preset_themes(self) -> List[Theme]:
        """Get list of preset (non-custom) themes.
        
        Returns:
            List of preset themes
        """
        return [t for t in self._themes.values() if not t.is_custom]
    
    def get_custom_themes(self) -> List[Theme]:
        """Get list of custom user themes.
        
        Returns:
            List of custom themes
        """
        return [t for t in self._themes.values() if t.is_custom]
    
    def save_custom_theme(self, theme: Theme) -> bool:
        """Save a custom theme.
        
        Args:
            theme: Theme to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            theme.is_custom = True
            theme_path = self.custom_themes_dir / f"{theme.name}.json"
            
            with open(theme_path, 'w', encoding='utf-8') as f:
                json.dump(theme.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Add/update in memory
            self._themes[theme.name] = theme
            return True
        except Exception as e:
            print(f"Error saving theme: {e}")
            return False
    
    def delete_custom_theme(self, name: str) -> bool:
        """Delete a custom theme.
        
        Args:
            name: Theme name to delete
            
        Returns:
            True if successful, False otherwise
        """
        theme = self._themes.get(name)
        if not theme or not theme.is_custom:
            return False
        
        try:
            theme_path = self.custom_themes_dir / f"{name}.json"
            if theme_path.exists():
                theme_path.unlink()
            
            # Remove from memory
            del self._themes[name]
            return True
        except Exception as e:
            print(f"Error deleting theme: {e}")
            return False
    
    def reload_themes(self):
        """Reload all themes from disk."""
        self._themes.clear()
        self._load_all_themes()


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance.
    
    Returns:
        ThemeManager instance
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
