"""Main entry point for Week Calendar application.

Provides kid-friendly calendar interface with day/week/month/year views.
"""

import sys
from pathlib import Path
from datetime import date

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QStackedWidget
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
        
        # Initialize screen time manager
        self.screentime_manager = ScreenTimeManager(self)
        
        self._init_ui()
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
        
        # Set dark theme styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2C3E50;
            }
            QPushButton {
                background-color: #34495E;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #1ABC9C;
            }
            QLabel {
                color: white;
            }
        """)
        
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
        """Handle settings button click - open parental settings or screentime."""
        # If screentime is running and timer is displayed, show quick actions
        if self.nav_bar.showing_timer and self.screentime_manager.is_running():
            self._show_screentime_quick_actions()
        else:
            # Otherwise show regular settings
            settings_dialog = SettingsDialog(self.database, self)
            settings_dialog.settings_changed.connect(self._on_settings_changed)
            settings_dialog.exec_()
    
    def _on_settings_changed(self):
        """Handle settings changes - refresh weather and views."""
        print("Settings changed - refreshing data...")
        # Reload screentime settings
        self.screentime_manager.load_settings()
        # TODO: Reload weather with new location settings
        # TODO: Refresh all views
        self._refresh_current_view()
    
    def _show_week_view(self):
        """Show week view from dashboard."""
        self.view_stack.setCurrentWidget(self.week_view)
        self.nav_bar.set_active_view("week")
        self.week_view.refresh()    
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
                self
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
