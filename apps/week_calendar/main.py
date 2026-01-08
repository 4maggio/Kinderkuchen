"""Main entry point for Week Calendar application.

Provides kid-friendly calendar interface with day/week/month/year views.
"""

import copy
import sys
from pathlib import Path
from datetime import date
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QStackedWidget, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models import CalendarDatabase
from utils.dummy_data import populate_database_with_dummy_data, populate_weather_cache
from utils.screentime import ScreenTimeManager
from widgets.navigation_bar import NavigationBar
from widgets.settings_dialog import SettingsDialog
from widgets.screentime_dialog import ScreenTimeQuickActionsDialog
from views.dashboard_view import DashboardView
from views.week_view import WeekView
from views.day_view import DayView
from views.month_view import MonthView
from views.year_view import YearView
from themes.theme_manager import get_theme_manager, Theme, ThemeColors


class WeekCalendarApp(QMainWindow):
    """Main calendar application window."""
    
    def __init__(self, windowed: bool = False):
        """Initialize the calendar app.
        
        Args:
            windowed: If True, run in 800x480 window. If False, run fullscreen.
        """
        super().__init__()
        
        self.windowed = windowed
        self.database = CalendarDatabase()
        self.current_date = date.today()
        
        # Initialize theme manager
        self.theme_manager = get_theme_manager()
        self.current_theme = None
        self.appearance_settings = {}
        self.icon_size_override = 64
        
        # Initialize screen time manager
        self.screentime_manager = ScreenTimeManager(self)
        
        self._init_ui()
        self._load_and_apply_theme()
        self._populate_dummy_data_if_needed()
        
        # Start screentime after UI is ready
        self.screentime_manager.start()
        
        # Connect screentime updates to navigation bar
        self.screentime_manager.time_updated.connect(self._on_screentime_update)
        self.screentime_manager.timer_stopped.connect(self._on_screentime_stopped)
        
    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Week Calendar")
        
        if self.windowed:
            self.resize(800, 480)
        else:
            self.showFullScreen()
        
        # Central widget with main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Navigation bar at top
        self.nav_bar = NavigationBar(self)
        self.nav_bar.view_changed.connect(self._on_view_changed)
        self.nav_bar.back_clicked.connect(self._on_back_clicked)
        self.nav_bar.settings_clicked.connect(self._on_settings_clicked)
        self.nav_bar.rotation_clicked.connect(self._rotate_display)
        main_layout.addWidget(self.nav_bar)
        
        # Store reference to quick actions dialog
        self.quick_actions_dialog = None
        
        # Stacked widget for different views
        self.view_stack = QStackedWidget()
        main_layout.addWidget(self.view_stack)
        
        # Create all views
        self.dashboard_view = DashboardView(self.database)
        self.day_view = DayView(self.database, self.current_date)
        self.week_view = WeekView(self.database, self.current_date)
        self.month_view = MonthView(self.database, self.current_date)
        self.year_view = YearView(self.database, self.current_date)
        
        # Add views to stack (dashboard first)
        self.view_stack.addWidget(self.dashboard_view)
        self.view_stack.addWidget(self.day_view)
        self.view_stack.addWidget(self.week_view)
        self.view_stack.addWidget(self.month_view)
        self.view_stack.addWidget(self.year_view)
        
        # Connect view navigation signals
        self.dashboard_view.calendar_clicked.connect(self._show_week_view)
        self.week_view.day_clicked.connect(self._show_day_view)
        self.month_view.day_clicked.connect(self._show_day_view)
        self.year_view.month_clicked.connect(self._show_month_view)
        
        # Start with dashboard view
        self.view_stack.setCurrentWidget(self.dashboard_view)
        self.nav_bar.set_active_view(None)  # No view active on dashboard
        
        # Apply saved rotation if any
        rotation = int(self.database.get_setting('rotation', '0'))
        if rotation != 0:
            self._apply_rotation(rotation)
    
    def _populate_dummy_data_if_needed(self):
        """Populate database with dummy data if empty."""
        # Check if database has any entries
        entries = self.database.get_entries_by_date(self.current_date)
        
        if not entries:
            print("Database empty - populating with dummy data...")
            populate_database_with_dummy_data(self.database, weeks=8)
            populate_weather_cache(self.database, days=30)
            
            # Refresh current view
            self._refresh_current_view()
    
    def _on_view_changed(self, view_name: str):
        """Handle view change from navigation bar.
        
        Args:
            view_name: Name of view to switch to ("day", "week", "month", "year")
        """
        view_map = {
            "day": self.day_view,
            "week": self.week_view,
            "month": self.month_view,
            "year": self.year_view
        }
        
        view = view_map.get(view_name)
        if view:
            self.view_stack.setCurrentWidget(view)
            view.refresh()
    
    def _on_back_clicked(self):
        """Handle back button click - return to dashboard."""
        current_view = self.view_stack.currentWidget()
        
        # If on dashboard, exit app
        if current_view == self.dashboard_view:
            print("Exiting Week Calendar app...")
            self.close()
        else:
            # Otherwise return to dashboard
            self.view_stack.setCurrentWidget(self.dashboard_view)
            self.nav_bar.set_active_view(None)
    
    def _on_settings_clicked(self):
        """Handle settings button click - show fullscreen settings or screentime."""
        # If screentime is running and timer is displayed, show quick actions
        if self.nav_bar.showing_timer and self.screentime_manager.is_running():
            self._show_screentime_quick_actions()
        else:
            # Show settings as fullscreen view
            self._show_settings_fullscreen()
    
    def _show_settings_fullscreen(self):
        """Show settings view in fullscreen mode."""
        # Store current theme for potential restore
        previous_theme = copy.deepcopy(self.current_theme)
        
        # Create settings view if it doesn't exist
        if not hasattr(self, 'settings_view'):
            self.settings_view = SettingsDialog(self.database, self, theme=self.current_theme)
            self.settings_view.settings_changed.connect(self._on_settings_changed)
            self.settings_view.close_requested.connect(self._on_settings_closed)
            self.settings_view.theme_preview_requested.connect(self._handle_theme_preview)
            self.settings_view.theme_preview_reset.connect(lambda: self._restore_theme_snapshot(previous_theme))
            self.view_stack.addWidget(self.settings_view)
        
        # Update theme in case it changed
        self.settings_view.theme = self.current_theme
        self.settings_view.theme_colors = self.current_theme.colors if self.current_theme else ThemeColors()
        self.settings_view._apply_theme_styles()
        
        # Hide navigation bar and show settings
        self.nav_bar.hide()
        self.view_stack.setCurrentWidget(self.settings_view)
        self._settings_previous_theme = previous_theme
    
    def _on_settings_closed(self):
        """Handle settings view close - return to previous view."""
        # Show navigation bar
        self.nav_bar.show()
        
        # Return to previous view (dashboard if unsure)
        if self.view_stack.currentWidget() == self.settings_view:
            self.view_stack.setCurrentWidget(self.dashboard_view)
            self.nav_bar.set_active_view(None)
    
    def _on_settings_changed(self):
        """Handle settings changes - refresh weather and views."""
        print("Settings changed - refreshing data...")
        # Reload screentime settings
        self.screentime_manager.load_settings()
        # Reload and apply theme in case it changed
        self._load_and_apply_theme()
        # Reload dashboard launcher config
        if hasattr(self.dashboard_view, 'launcher_config'):
            self.dashboard_view.launcher_config = self.dashboard_view._load_launcher_config()
            self.dashboard_view._build_app_grid()
            # Re-apply theme and icon size to new tiles
            self.dashboard_view.apply_theme(self.current_theme)
            if hasattr(self, 'icon_size_override'):
                self.dashboard_view.set_icon_size(self.icon_size_override)
        # TODO: Reload weather with new location settings
        # TODO: Refresh all views
        self._refresh_current_view()
    
    def _handle_theme_preview(self, theme_name: str, overrides: dict):
        """Apply a live preview theme without persisting it."""
        theme = self.theme_manager.get_theme(theme_name)
        if not theme:
            return
        self._apply_theme(theme, overrides)
    
    def _restore_theme_snapshot(self, snapshot: Optional[Theme]):
        """Restore the last persisted theme when cancelling previews."""
        if snapshot:
            self._apply_theme(snapshot, self.appearance_settings)
        else:
            self._load_and_apply_theme()
    
    def _show_week_view(self):
        """Show week view from dashboard."""
        self.view_stack.setCurrentWidget(self.week_view)
        self.nav_bar.set_active_view("week")
        self.week_view.refresh()    
    def _load_and_apply_theme(self):
        """Load theme from settings and apply it to the application."""
        # Load theme name from settings.json
        import json
        settings_path = Path(__file__).parent / "config" / "settings.json"
        default_theme = "princess"
        theme_name = default_theme
        self.appearance_settings = {}
        
        try:
            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    appearance = settings.get("appearance", {}) or {}
                    self.appearance_settings = appearance
                    theme_name = appearance.get("theme", default_theme)
        except Exception as e:
            print(f"Error loading theme setting: {e}")
            self.appearance_settings = {}
        
        if not theme_name:
            theme_name = default_theme
        
        # Get theme from theme manager
        theme = self.theme_manager.get_theme(theme_name)
        
        # Fallback to princess preset first, then dark theme
        if theme is None and theme_name != default_theme:
            print(f"Theme '{theme_name}' not found, switching to '{default_theme}'")
            theme = self.theme_manager.get_theme(default_theme)

        if theme is None:
            print("Princess theme missing, falling back to 'dark'")
            theme = self.theme_manager.get_theme("dark")
        
        # If still None, create a default dark theme
        if theme is None:
            from themes.theme_manager import Theme
            theme = Theme(name=default_theme, display_name="Princess")
        
        self._apply_theme(theme, self.appearance_settings)
    
    def _apply_theme(self, theme: Theme, overrides: Optional[dict] = None):
        """Apply theme to the application with optional appearance overrides."""
        if theme is None:
            return
        effective_overrides = overrides if overrides is not None else self.appearance_settings
        applied_theme = self._merge_theme_overrides(theme, effective_overrides)
        self.current_theme = applied_theme
        
        stylesheet = applied_theme.generate_stylesheet()
        self.setStyleSheet(stylesheet)
        
        font = QFont(applied_theme.font.family, applied_theme.font.size_normal)
        QApplication.instance().setFont(font)
        
        self._apply_theme_to_components(applied_theme)
        self._apply_icon_size(effective_overrides)
        print(f"Applied theme: {applied_theme.display_name}")

    def _merge_theme_overrides(self, theme: Theme, overrides: Optional[dict]) -> Theme:
        """Combine base theme values with appearance overrides from settings."""
        merged_theme = copy.deepcopy(theme)
        if not overrides:
            return merged_theme
        if overrides.get("font_family"):
            merged_theme.font.family = overrides["font_family"]
        if "font_size" in overrides and overrides["font_size"]:
            try:
                requested_size = int(overrides["font_size"])
            except (TypeError, ValueError):
                requested_size = merged_theme.font.size_normal
            delta = requested_size - merged_theme.font.size_normal
            merged_theme.font.size_normal = requested_size
            merged_theme.font.size_small = max(6, merged_theme.font.size_small + delta)
            merged_theme.font.size_large = max(8, merged_theme.font.size_large + delta)
            merged_theme.font.size_xlarge = max(10, merged_theme.font.size_xlarge + delta)
            merged_theme.font.size_heading = max(12, merged_theme.font.size_heading + delta)
            merged_theme.font.size_title = max(14, merged_theme.font.size_title + delta)
        
        # Apply font scaling percentages
        font_scale_small = overrides.get("font_scale_small", 0)
        font_scale_large = overrides.get("font_scale_large", 50)
        
        try:
            scale_small = float(font_scale_small) / 100.0
            scale_large = float(font_scale_large) / 100.0
            
            # Apply to smaller fonts (menus, labels, etc.)
            merged_theme.font.size_small = max(6, int(merged_theme.font.size_small * (1 + scale_small)))
            
            # Apply to larger fonts (tiles, icons, headers)
            merged_theme.font.size_large = max(8, int(merged_theme.font.size_large * (1 + scale_large)))
            merged_theme.font.size_xlarge = max(10, int(merged_theme.font.size_xlarge * (1 + scale_large)))
            merged_theme.font.size_heading = max(12, int(merged_theme.font.size_heading * (1 + scale_large)))
            merged_theme.font.size_title = max(14, int(merged_theme.font.size_title * (1 + scale_large)))
        except (TypeError, ValueError, ZeroDivisionError):
            pass  # Keep defaults if scaling fails
        
        return merged_theme
    
    def _apply_theme_to_components(self, theme):
        """Propagate theme updates to child widgets."""
        targets = [
            getattr(self, 'nav_bar', None),
            getattr(self, 'dashboard_view', None),
            getattr(self, 'day_view', None),
            getattr(self, 'week_view', None),
            getattr(self, 'month_view', None),
            getattr(self, 'year_view', None)
        ]
        for widget in targets:
            if widget and hasattr(widget, 'apply_theme'):
                widget.apply_theme(theme)
        if hasattr(self, 'screentime_manager') and self.screentime_manager:
            self.screentime_manager.set_theme(theme)

    def _apply_icon_size(self, overrides: Optional[dict]):
        """Propagate the configured icon sizes to widgets that support it."""
        # Get the three separate icon sizes
        tile_size = self._resolve_icon_size(overrides, 'tile_icon_size', 64, 32, 120)
        hero_size = self._resolve_icon_size(overrides, 'hero_icon_size', 96, 64, 160)
        calendar_size = self._resolve_icon_size(overrides, 'calendar_icon_size', 48, 24, 96)
        
        # Apply to dashboard (has both tiles and hero icons)
        dashboard = getattr(self, 'dashboard_view', None)
        if dashboard:
            if hasattr(dashboard, 'set_tile_icon_size'):
                dashboard.set_tile_icon_size(tile_size)
            if hasattr(dashboard, 'set_hero_icon_size'):
                dashboard.set_hero_icon_size(hero_size)
        
        # Apply calendar icon size to all calendar views
        calendar_views = [
            getattr(self, 'day_view', None),
            getattr(self, 'week_view', None),
            getattr(self, 'month_view', None),
            getattr(self, 'year_view', None)
        ]
        for view in calendar_views:
            if view and hasattr(view, 'set_calendar_icon_size'):
                view.set_calendar_icon_size(calendar_size)

    def _resolve_icon_size(self, overrides: Optional[dict], key: str, default: int, min_val: int, max_val: int) -> int:
        """Resolve icon size from overrides/settings with sane fallbacks."""
        candidates = []
        if overrides:
            candidates.append(overrides.get(key))
        if self.appearance_settings:
            candidates.append(self.appearance_settings.get(key))
        for value in candidates:
            try:
                sanitized = int(value)
            except (TypeError, ValueError):
                continue
            if sanitized > 0:
                return max(min_val, min(max_val, sanitized))
        return default
    
    def _rotate_display(self):
        """Rotate display 90 degrees clockwise."""
        # Get current rotation from database settings
        current_rotation = int(self.database.get_setting('rotation', '0'))
        
        # Cycle through rotations: 0 -> 90 -> 180 -> 270 -> 0
        new_rotation = (current_rotation + 90) % 360
        
        # Save new rotation
        self.database.set_setting('rotation', str(new_rotation))
        
        # Apply rotation
        self._apply_rotation(new_rotation)
    
    def _apply_rotation(self, rotation: int):
        """Apply rotation transform to main window."""
        from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
        from PyQt5.QtGui import QTransform
        
        # Get central widget
        central = self.centralWidget()
        if not central:
            return
        
        # Create transform
        transform = QTransform()
        
        if rotation == 90:
            # Rotate 90° clockwise
            transform.rotate(90)
        elif rotation == 180:
            # Rotate 180°
            transform.rotate(180)
        elif rotation == 270:
            # Rotate 270° clockwise
            transform.rotate(270)
        
        # Apply transform to central widget's graphics effect
        # Note: This is a simple rotation. For production on Pi, 
        # you would modify /boot/config.txt display_rotate setting
        if hasattr(central, 'setTransform'):
            central.setTransform(transform)
        else:
            print(f"Display rotation set to {rotation}° (would apply on actual Pi hardware)")    
    def _show_day_view(self, target_date: date):
        """Show day view for a specific date.
        
        Args:
            target_date: Date to display
        """
        self.current_date = target_date
        self.day_view.set_date(target_date)
        self.view_stack.setCurrentWidget(self.day_view)
        self.nav_bar.set_active_view("day")
    
    def _show_month_view(self, year: int, month: int):
        """Show month view for a specific month.
        
        Args:
            year: Year to display
            month: Month to display (1-12)
        """
        target_date = date(year, month, 1)
        self.month_view.set_date(target_date)
        self.view_stack.setCurrentWidget(self.month_view)
        self.nav_bar.set_active_view("month")
    
    def _refresh_current_view(self):
        """Refresh the currently visible view."""
        current_view = self.view_stack.currentWidget()
        if hasattr(current_view, 'refresh'):
            current_view.refresh()
    
    def _on_screentime_update(self, remaining_seconds: int, total_seconds: int):
        """Handle screentime timer updates.
        
        Args:
            remaining_seconds: Remaining seconds
            total_seconds: Total seconds
        """
        # Only update display if screentime is enabled
        if not self.screentime_manager.enabled:
            return
        
        # Update navigation bar display
        self.nav_bar.update_screentime_display(remaining_seconds)
        
        # Update quick actions dialog if open
        if self.quick_actions_dialog and self.quick_actions_dialog.isVisible():
            self.quick_actions_dialog.update_time(remaining_seconds, total_seconds)
    
    def _on_screentime_stopped(self):
        """Handle screentime timer stopped."""
        self.nav_bar.reset_settings_display()
        
        if self.quick_actions_dialog:
            self.quick_actions_dialog.close()
            self.quick_actions_dialog = None
    
    def _show_screentime_quick_actions(self):
        """Show screentime quick actions dialog."""
        try:
            # Pause timer while dialog is open
            self.screentime_manager.pause()
            
            remaining_seconds = self.screentime_manager.get_remaining_time()
            total_seconds = self.screentime_manager.limit_minutes * 60
            
            self.quick_actions_dialog = ScreenTimeQuickActionsDialog(
                remaining_seconds,
                total_seconds,
                self,
                theme=self.current_theme
            )
            
            # Connect signals
            self.quick_actions_dialog.time_added.connect(self._on_time_added)
            self.quick_actions_dialog.timer_cancelled.connect(self._on_timer_cancelled)
            self.quick_actions_dialog.credit_tomorrow.connect(self._on_credit_tomorrow)
            
            self.quick_actions_dialog.exec_()
            
            # Resume timer after dialog closes
            if self.screentime_manager.is_running():
                self.screentime_manager.resume()
        except Exception as e:
            print(f"Error showing screentime quick actions: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_time_added(self, minutes: int):
        """Handle time added to current session.
        
        Args:
            minutes: Minutes to add
        """
        self.screentime_manager.add_time(minutes)
        
        # Also update today's used time to reflect the added time
        # (so it doesn't count against the daily limit)
        from datetime import date
        today = date.today()
        self.screentime_manager.controller.add_used_time(-minutes, today)
    
    def _on_timer_cancelled(self):
        """Handle timer cancellation."""
        self.screentime_manager.stop()
    
    def _on_credit_tomorrow(self, minutes: int):
        """Handle crediting time for tomorrow.
        
        Args:
            minutes: Minutes to credit
        """
        from datetime import date, timedelta
        tomorrow = date.today() + timedelta(days=1)
        self.screentime_manager.controller.credit_time_for_day(minutes, tomorrow)


def main():
    """Main entry point."""
    # Check for command line arguments
    windowed = "--windowed" in sys.argv
    
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Arial", 12)
    app.setFont(font)
    
    # Create and show main window
    window = WeekCalendarApp(windowed=windowed)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
