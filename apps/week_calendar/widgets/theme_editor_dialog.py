"""
Theme Editor Dialog

Allows users to create and edit custom themes with colors, fonts, and decorations.
"""

from functools import partial
from pathlib import Path
from typing import List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTabWidget, QWidget, QGroupBox,
    QFormLayout, QSpinBox, QMessageBox, QColorDialog, QCheckBox,
    QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from themes.theme_manager import Theme, ThemeColors, ThemeFont, ThemeDecoration

ARTWORK_ROOT = Path(__file__).resolve().parent.parent / "resources" / "artwork"


class ColorButton(QPushButton):
    """Button for selecting colors."""
    
    color_changed = pyqtSignal(str)  # Emits hex color
    
    def __init__(self, initial_color: str = "#FFFFFF", parent=None):
        """Initialize color button.
        
        Args:
            initial_color: Initial color in hex format
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._color = initial_color
        self.setFixedSize(60, 30)
        self.clicked.connect(self._choose_color)
        self._update_style()
    
    def _update_style(self):
        """Update button style to show current color."""
        # Calculate text color (white or black) based on background brightness
        color = QColor(self._color)
        brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
        text_color = "#000000" if brightness > 128 else "#FFFFFF"
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                color: {text_color};
                border: 2px solid #888;
                border-radius: 4px;
                font-size: 10px;
            }}
        """)
        self.setText(self._color[:7])
    
    def _choose_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(QColor(self._color), self, "Farbe wählen")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)
    
    def get_color(self) -> str:
        """Get current color.
        
        Returns:
            Color in hex format
        """
        return self._color
    
    def set_color(self, color: str):
        """Set color.
        
        Args:
            color: Color in hex format
        """
        self._color = color
        self._update_style()


class ThemeEditorDialog(QDialog):
    """Dialog for creating/editing custom themes."""
    
    theme_saved = pyqtSignal(Theme)  # Emitted when theme is saved
    
    def __init__(self, theme: Theme = None, parent=None):
        """Initialize theme editor.
        
        Args:
            theme: Theme to edit (None for new theme)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.theme = theme if theme else Theme(name="custom", display_name="Mein Theme", is_custom=True)
        self.is_new = theme is None
        self.artwork_root = ARTWORK_ROOT
        self.available_artwork = self._discover_artwork_files()
        
        self.setWindowTitle("Theme bearbeiten" if not self.is_new else "Neues Theme erstellen")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        
        self._init_ui()
        self._load_theme_data()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Tab widget for different settings
        tabs = QTabWidget()
        
        # Basic info tab
        basic_tab = self._create_basic_tab()
        tabs.addTab(basic_tab, "Grundeinstellungen")
        
        # Colors tab
        colors_tab = self._create_colors_tab()
        tabs.addTab(colors_tab, "Farben")
        
        # Font tab
        font_tab = self._create_font_tab()
        tabs.addTab(font_tab, "Schriftart")
        
        # Decoration tab
        decoration_tab = self._create_decoration_tab()
        tabs.addTab(decoration_tab, "Dekoration")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        preview_btn = QPushButton("Vorschau")
        preview_btn.clicked.connect(self._preview_theme)
        button_layout.addWidget(preview_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self._save_theme)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_basic_tab(self) -> QWidget:
        """Create basic info tab.
        
        Returns:
            Widget with basic info controls
        """
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Theme name (ID)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("z.B. mein_theme")
        if not self.is_new:
            self.name_input.setEnabled(False)  # Can't change name of existing theme
        layout.addRow("Name (ID):", self.name_input)
        
        # Display name
        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("z.B. Mein tolles Theme")
        layout.addRow("Anzeigename:", self.display_name_input)
        
        # Description
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Kurze Beschreibung")
        layout.addRow("Beschreibung:", self.description_input)
        
        # Author
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Dein Name")
        layout.addRow("Autor:", self.author_input)
        
        return widget
    
    def _create_colors_tab(self) -> QWidget:
        """Create colors tab.
        
        Returns:
            Widget with color controls
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        
        # Background colors
        bg_group = QGroupBox("Hintergrundfarben")
        bg_layout = QFormLayout()
        
        self.color_background = ColorButton()
        bg_layout.addRow("Haupthintergrund:", self.color_background)
        
        self.color_background_secondary = ColorButton()
        bg_layout.addRow("Sekundär:", self.color_background_secondary)
        
        self.color_background_hover = ColorButton()
        bg_layout.addRow("Hover:", self.color_background_hover)
        
        bg_group.setLayout(bg_layout)
        main_layout.addWidget(bg_group)
        
        # Text colors
        text_group = QGroupBox("Textfarben")
        text_layout = QFormLayout()
        
        self.color_text_primary = ColorButton()
        text_layout.addRow("Primär:", self.color_text_primary)
        
        self.color_text_secondary = ColorButton()
        text_layout.addRow("Sekundär:", self.color_text_secondary)
        
        self.color_text_disabled = ColorButton()
        text_layout.addRow("Deaktiviert:", self.color_text_disabled)
        
        text_group.setLayout(text_layout)
        main_layout.addWidget(text_group)
        
        # Accent colors
        accent_group = QGroupBox("Akzentfarben")
        accent_layout = QFormLayout()
        
        self.color_accent = ColorButton()
        accent_layout.addRow("Akzent:", self.color_accent)
        
        self.color_accent_hover = ColorButton()
        accent_layout.addRow("Akzent Hover:", self.color_accent_hover)
        
        self.color_accent_light = ColorButton()
        accent_layout.addRow("Akzent Hell:", self.color_accent_light)
        
        accent_group.setLayout(accent_layout)
        main_layout.addWidget(accent_group)
        
        # Status colors
        status_group = QGroupBox("Statusfarben")
        status_layout = QFormLayout()
        
        self.color_success = ColorButton()
        status_layout.addRow("Erfolg:", self.color_success)
        
        self.color_warning = ColorButton()
        status_layout.addRow("Warnung:", self.color_warning)
        
        self.color_error = ColorButton()
        status_layout.addRow("Fehler:", self.color_error)
        
        self.color_info = ColorButton()
        status_layout.addRow("Info:", self.color_info)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        main_layout.addStretch()
        
        return widget
    
    def _create_font_tab(self) -> QWidget:
        """Create font tab.
        
        Returns:
            Widget with font controls
        """
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Font family
        self.font_family = QComboBox()
        self.font_family.addItems([
            "Arial",
            "Comic Sans MS",
            "Georgia",
            "Times New Roman",
            "Verdana",
            "Courier New"
        ])
        self.font_family.setEditable(True)
        layout.addRow("Schriftart:", self.font_family)
        
        # Font sizes
        self.font_size_small = QSpinBox()
        self.font_size_small.setRange(8, 20)
        layout.addRow("Größe Klein:", self.font_size_small)
        
        self.font_size_normal = QSpinBox()
        self.font_size_normal.setRange(10, 24)
        layout.addRow("Größe Normal:", self.font_size_normal)
        
        self.font_size_large = QSpinBox()
        self.font_size_large.setRange(12, 28)
        layout.addRow("Größe Groß:", self.font_size_large)
        
        self.font_size_xlarge = QSpinBox()
        self.font_size_xlarge.setRange(14, 32)
        layout.addRow("Größe Sehr Groß:", self.font_size_xlarge)
        
        self.font_size_heading = QSpinBox()
        self.font_size_heading.setRange(16, 36)
        layout.addRow("Größe Überschrift:", self.font_size_heading)
        
        self.font_size_title = QSpinBox()
        self.font_size_title.setRange(18, 40)
        layout.addRow("Größe Titel:", self.font_size_title)
        
        return widget
    
    def _create_decoration_tab(self) -> QWidget:
        """Create decoration tab.
        
        Returns:
            Widget with decoration controls
        """
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Decoration style
        self.decoration_style = QComboBox()
        self.decoration_style.addItems([
            "Keine",
            "Dinosaurier",
            "Prinzessin",
            "Fußball",
            "Pferde",
            "Weltraum",
            "Ozean"
        ])
        layout.addRow("Deko-Stil:", self.decoration_style)
        
        # Icon style
        self.icon_style = QComboBox()
        self.icon_style.addItems([
            "Standard",
            "Abgerundet",
            "Flach",
            "Umriss"
        ])
        layout.addRow("Icon-Stil:", self.icon_style)
        
        # Corner decoration
        self.corner_decoration = QCheckBox("Eck-Dekorationen anzeigen")
        layout.addRow("", self.corner_decoration)
        
        # Border style
        self.border_style = QComboBox()
        self.border_style.addItems([
            "Durchgezogen",
            "Gestrichelt",
            "Dekoriert"
        ])
        layout.addRow("Rahmen-Stil:", self.border_style)

        # Artwork selections
        artwork_group = QGroupBox("Artwork & Sticker")
        artwork_form = QFormLayout()
        self.background_artwork_combo = self._create_artwork_combo()
        artwork_form.addRow("Hintergrund:", self._build_artwork_row(self.background_artwork_combo))
        self.hero_left_combo = self._create_artwork_combo()
        artwork_form.addRow("Linke Figur:", self._build_artwork_row(self.hero_left_combo))
        self.hero_right_combo = self._create_artwork_combo()
        artwork_form.addRow("Rechte Figur:", self._build_artwork_row(self.hero_right_combo))
        self.sticker_combos = []
        for idx in range(3):
            combo = self._create_artwork_combo()
            self.sticker_combos.append(combo)
            artwork_form.addRow(f"Sticker {idx + 1}:", self._build_artwork_row(combo))
        artwork_group.setLayout(artwork_form)
        layout.addRow(artwork_group)
        
        return widget

    def _create_artwork_combo(self) -> QComboBox:
        """Create a combo box pre-populated with available artwork files."""
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItem("Standard", "")
        for rel_path in self.available_artwork:
            combo.addItem(rel_path, rel_path)
        return combo

    def _build_artwork_row(self, combo: QComboBox) -> QWidget:
        """Wrap an artwork combo with a browse button."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(combo, 1)
        browse_btn = QPushButton("Durchsuchen…")
        browse_btn.clicked.connect(partial(self._browse_for_artwork, combo))
        row.addWidget(browse_btn)
        return container

    def _browse_for_artwork(self, combo: QComboBox):
        """Allow the user to pick a custom PNG file."""
        start_dir = str(self.artwork_root if self.artwork_root.exists() else Path.home())
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Grafik auswählen",
            start_dir,
            "Bilder (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return
        rel_path = self._relative_artwork_path(file_path)
        self._ensure_combo_has_value(combo, rel_path)
        index = combo.findData(rel_path)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentText(rel_path)

    def _ensure_combo_has_value(self, combo: QComboBox, value: str):
        """Ensure a combo contains a specific value option."""
        if combo.findData(value) == -1:
            combo.addItem(value, value)

    def _set_combo_value(self, combo: QComboBox, value: Optional[str]):
        """Set the combo's current selection to value or fallback to default."""
        if not value:
            combo.setCurrentIndex(0)
            return
        self._ensure_combo_has_value(combo, value)
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentText(value)

    def _relative_artwork_path(self, file_path: str) -> str:
        """Return path relative to artwork root when possible."""
        candidate = Path(file_path).resolve()
        try:
            return candidate.relative_to(self.artwork_root.resolve()).as_posix()
        except ValueError:
            return candidate.as_posix()

    def _get_artwork_combo_value(self, combo: QComboBox) -> Optional[str]:
        """Return the currently selected artwork path, if any."""
        value = combo.currentData()
        if value:
            return value
        text = combo.currentText().strip()
        return text or None

    def _discover_artwork_files(self) -> List[str]:
        """Discover built-in artwork PNGs for quick selection."""
        if not self.artwork_root.exists():
            return []
        files = [
            path.relative_to(self.artwork_root).as_posix()
            for path in sorted(self.artwork_root.rglob("*.png"))
        ]
        return files
    
    def _load_theme_data(self):
        """Load theme data into UI controls."""
        # Basic info
        self.name_input.setText(self.theme.name)
        self.display_name_input.setText(self.theme.display_name)
        self.description_input.setText(self.theme.description)
        self.author_input.setText(self.theme.author)
        
        # Colors
        c = self.theme.colors
        self.color_background.set_color(c.background)
        self.color_background_secondary.set_color(c.background_secondary)
        self.color_background_hover.set_color(c.background_hover)
        self.color_text_primary.set_color(c.text_primary)
        self.color_text_secondary.set_color(c.text_secondary)
        self.color_text_disabled.set_color(c.text_disabled)
        self.color_accent.set_color(c.accent)
        self.color_accent_hover.set_color(c.accent_hover)
        self.color_accent_light.set_color(c.accent_light)
        self.color_success.set_color(c.success)
        self.color_warning.set_color(c.warning)
        self.color_error.set_color(c.error)
        self.color_info.set_color(c.info)
        
        # Font
        f = self.theme.font
        index = self.font_family.findText(f.family)
        if index >= 0:
            self.font_family.setCurrentIndex(index)
        else:
            self.font_family.setCurrentText(f.family)
        
        self.font_size_small.setValue(f.size_small)
        self.font_size_normal.setValue(f.size_normal)
        self.font_size_large.setValue(f.size_large)
        self.font_size_xlarge.setValue(f.size_xlarge)
        self.font_size_heading.setValue(f.size_heading)
        self.font_size_title.setValue(f.size_title)
        
        # Decoration
        d = self.theme.decoration
        style_map = {
            "none": 0, "dinosaurs": 1, "princess": 2, 
            "football": 3, "horses": 4, "space": 5, "ocean": 6
        }
        self.decoration_style.setCurrentIndex(style_map.get(d.style, 0))
        
        icon_map = {"default": 0, "rounded": 1, "flat": 2, "outline": 3}
        self.icon_style.setCurrentIndex(icon_map.get(d.icon_style, 0))
        
        self.corner_decoration.setChecked(d.corner_decoration)
        
        border_map = {"solid": 0, "dashed": 1, "decorated": 2}
        self.border_style.setCurrentIndex(border_map.get(d.border_style, 0))

        self._set_combo_value(self.background_artwork_combo, d.background_pattern)
        self._set_combo_value(self.hero_left_combo, d.hero_left_image)
        self._set_combo_value(self.hero_right_combo, d.hero_right_image)
        stickers = d.sticker_images or []
        for idx, combo in enumerate(self.sticker_combos):
            value = stickers[idx] if idx < len(stickers) else ""
            self._set_combo_value(combo, value)
    
    def _save_theme(self):
        """Save theme and close dialog."""
        # Validate
        name = self.name_input.text().strip()
        display_name = self.display_name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Fehler", "Bitte einen Namen eingeben!")
            return
        
        if not display_name:
            QMessageBox.warning(self, "Fehler", "Bitte einen Anzeigenamen eingeben!")
            return
        
        # Update theme object
        self.theme.name = name
        self.theme.display_name = display_name
        self.theme.description = self.description_input.text().strip()
        self.theme.author = self.author_input.text().strip()
        
        # Update colors
        c = self.theme.colors
        c.background = self.color_background.get_color()
        c.background_secondary = self.color_background_secondary.get_color()
        c.background_hover = self.color_background_hover.get_color()
        c.text_primary = self.color_text_primary.get_color()
        c.text_secondary = self.color_text_secondary.get_color()
        c.text_disabled = self.color_text_disabled.get_color()
        c.accent = self.color_accent.get_color()
        c.accent_hover = self.color_accent_hover.get_color()
        c.accent_light = self.color_accent_light.get_color()
        c.success = self.color_success.get_color()
        c.warning = self.color_warning.get_color()
        c.error = self.color_error.get_color()
        c.info = self.color_info.get_color()
        
        # Update font
        f = self.theme.font
        f.family = self.font_family.currentText()
        f.size_small = self.font_size_small.value()
        f.size_normal = self.font_size_normal.value()
        f.size_large = self.font_size_large.value()
        f.size_xlarge = self.font_size_xlarge.value()
        f.size_heading = self.font_size_heading.value()
        f.size_title = self.font_size_title.value()
        
        # Update decoration
        d = self.theme.decoration
        style_reverse_map = ["none", "dinosaurs", "princess", "football", "horses", "space", "ocean"]
        d.style = style_reverse_map[self.decoration_style.currentIndex()]
        
        icon_reverse_map = ["default", "rounded", "flat", "outline"]
        d.icon_style = icon_reverse_map[self.icon_style.currentIndex()]
        
        d.corner_decoration = self.corner_decoration.isChecked()
        
        border_reverse_map = ["solid", "dashed", "decorated"]
        d.border_style = border_reverse_map[self.border_style.currentIndex()]
        d.background_pattern = self._get_artwork_combo_value(self.background_artwork_combo)
        d.hero_left_image = self._get_artwork_combo_value(self.hero_left_combo)
        d.hero_right_image = self._get_artwork_combo_value(self.hero_right_combo)
        sticker_values = [self._get_artwork_combo_value(combo) for combo in self.sticker_combos]
        d.sticker_images = [value for value in sticker_values if value]
        
        # Emit signal and close
        self.theme_saved.emit(self.theme)
        self.accept()
    
    def _preview_theme(self):
        """Show a preview of the theme."""
        # Create temporary theme with current settings
        temp_theme = Theme(
            name="preview",
            display_name=self.display_name_input.text() or "Vorschau",
            is_custom=True
        )
        
        # Copy current color settings
        temp_theme.colors.background = self.color_background.get_color()
        temp_theme.colors.background_secondary = self.color_background_secondary.get_color()
        temp_theme.colors.accent = self.color_accent.get_color()
        temp_theme.colors.text_primary = self.color_text_primary.get_color()
        
        # Apply temporarily to dialog
        stylesheet = temp_theme.generate_stylesheet()
        self.setStyleSheet(stylesheet)
        
        QMessageBox.information(
            self,
            "Vorschau",
            "Dies ist eine Vorschau des Themes.\n\n"
            "Die vollständige Vorschau ist sichtbar, wenn Sie das Theme speichern und in den Einstellungen auswählen."
        )
