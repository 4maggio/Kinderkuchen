"""Extended screen time management with daily allowances and usage time restrictions.

Manages:
- Daily allowed screen time (daily/weekly/calendar-based)
- Usage time windows (when app can be used)
- Time credits for tomorrow
- PIN-protected access outside allowed times
"""

import json
from pathlib import Path
from datetime import datetime, date, time
from typing import Dict, Tuple, Optional

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal


class ScreenTimeController(QWidget):
    """Controller for screen time with daily allowances and usage restrictions."""
    
    access_denied = pyqtSignal(str)  # Emits reason when access denied
    
    def __init__(self, parent=None):
        """Initialize controller.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        self.screentime_data_path = Path(__file__).parent.parent / "config" / "screentime_data.json"
        
        self.load_settings()
        self.load_screentime_data()
    
    def load_settings(self):
        """Load screentime settings from config."""
        try:
            with open(self.settings_path) as f:
                settings = json.load(f)
                st = settings.get("screentime", {})
                
                self.enabled = st.get("enabled", False)
                self.allowed_time_mode = st.get("allowed_time_mode", "daily")
                self.daily_allowed_minutes = st.get("daily_allowed_minutes", 30)
                self.weekly_allowed_minutes = st.get("weekly_allowed_minutes", {})
                self.calendar_category = st.get("calendar_category", "Screentime")
                
                self.usage_times_mode = st.get("usage_times_mode", "always")
                self.daily_usage_times = st.get("daily_usage_times", {"start": "00:00", "end": "23:59"})
                self.weekly_usage_times = st.get("weekly_usage_times", {})
        except Exception as e:
            print(f"Error loading screentime settings: {e}")
            self.enabled = False
            self.allowed_time_mode = "daily"
            self.daily_allowed_minutes = 30
    
    def load_screentime_data(self):
        """Load screentime usage data (used minutes per day)."""
        try:
            if self.screentime_data_path.exists():
                with open(self.screentime_data_path) as f:
                    self.screentime_data = json.load(f)
            else:
                self.screentime_data = {}
        except Exception as e:
            print(f"Error loading screentime data: {e}")
            self.screentime_data = {}
    
    def save_screentime_data(self):
        """Save screentime usage data."""
        try:
            self.screentime_data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.screentime_data_path, 'w') as f:
                json.dump(self.screentime_data, f, indent=2)
        except Exception as e:
            print(f"Error saving screentime data: {e}")
    
    def get_allowed_minutes_for_day(self, target_date: date) -> int:
        """Get allowed screen time minutes for a specific day.
        
        Args:
            target_date: Date to check
            
        Returns:
            Allowed minutes for that day
        """
        if self.allowed_time_mode == "daily":
            return self.daily_allowed_minutes
        
        elif self.allowed_time_mode == "weekly":
            weekday_names = ["monday", "tuesday", "wednesday", "thursday", 
                           "friday", "saturday", "sunday"]
            weekday = weekday_names[target_date.weekday()]
            return self.weekly_allowed_minutes.get(weekday, 30)
        
        elif self.allowed_time_mode == "calendar":
            # TODO: Implement calendar-based lookup
            # For now, return default
            return self.daily_allowed_minutes
        
        return 30  # Fallback
    
    def get_used_minutes_for_day(self, target_date: date) -> int:
        """Get used screen time minutes for a specific day.
        
        Args:
            target_date: Date to check
            
        Returns:
            Used minutes for that day
        """
        date_str = target_date.isoformat()
        return self.screentime_data.get(date_str, {}).get("used_minutes", 0)
    
    def get_remaining_minutes_for_day(self, target_date: date) -> int:
        """Get remaining screen time minutes for a specific day.
        
        Args:
            target_date: Date to check
            
        Returns:
            Remaining minutes for that day
        """
        allowed = self.get_allowed_minutes_for_day(target_date)
        used = self.get_used_minutes_for_day(target_date)
        
        # Add any credits for this day
        date_str = target_date.isoformat()
        credits = self.screentime_data.get(date_str, {}).get("credits", 0)
        
        return max(0, allowed + credits - used)
    
    def add_used_time(self, minutes: int, target_date: date = None):
        """Add used time for a day.
        
        Args:
            minutes: Minutes to add
            target_date: Date (default: today)
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        if date_str not in self.screentime_data:
            self.screentime_data[date_str] = {"used_minutes": 0, "credits": 0}
        
        self.screentime_data[date_str]["used_minutes"] += minutes
        self.save_screentime_data()
    
    def credit_time_for_day(self, minutes: int, target_date: date):
        """Credit time for a specific day.
        
        Args:
            minutes: Minutes to credit
            target_date: Target date
        """
        date_str = target_date.isoformat()
        
        if date_str not in self.screentime_data:
            self.screentime_data[date_str] = {"used_minutes": 0, "credits": 0}
        
        self.screentime_data[date_str]["credits"] += minutes
        self.save_screentime_data()
    
    def is_within_usage_times(self, check_time: datetime = None) -> Tuple[bool, Optional[str]]:
        """Check if current time is within allowed usage times.
        
        Args:
            check_time: Time to check (default: now)
            
        Returns:
            (is_allowed, reason_if_not)
        """
        if not self.enabled:
            return (True, None)
        
        if check_time is None:
            check_time = datetime.now()
        
        if self.usage_times_mode == "always":
            return (True, None)
        
        elif self.usage_times_mode == "weekly":
            weekday_names = ["monday", "tuesday", "wednesday", "thursday", 
                           "friday", "saturday", "sunday"]
            weekday = weekday_names[check_time.weekday()]
            times = self.weekly_usage_times.get(weekday, {"start": "00:00", "end": "23:59"})
            
            start_time = datetime.strptime(times["start"], "%H:%M").time()
            end_time = datetime.strptime(times["end"], "%H:%M").time()
            current_time = check_time.time()
            
            if start_time <= current_time <= end_time:
                return (True, None)
            else:
                return (False, f"Außerhalb der erlaubten Nutzungszeit ({times['start']} - {times['end']})")
        
        elif self.usage_times_mode == "calendar":
            # TODO: Implement calendar-based lookup
            return (True, None)
        
        return (True, None)
    
    def can_start_session(self) -> Tuple[bool, Optional[str]]:
        """Check if a session can be started now.
        
        Returns:
            (can_start, reason_if_not)
        """
        if not self.enabled:
            return (True, None)
        
        # Check usage times
        allowed, reason = self.is_within_usage_times()
        if not allowed:
            return (False, reason)
        
        # Check remaining time for today
        today = date.today()
        remaining = self.get_remaining_minutes_for_day(today)
        
        if remaining <= 0:
            return (False, "Bildschirmzeit für heute aufgebraucht")
        
        return (True, None)
