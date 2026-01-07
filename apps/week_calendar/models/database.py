"""
SQLite database schema and query functions for Week Calendar app.

Handles calendar entries, weather data, and app settings storage.
Optimized for Pi2 performance with proper indexing.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime
from contextlib import contextmanager


class CalendarDatabase:
    """Manages SQLite database for calendar data."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. 
                    Defaults to data/calendar.db in app directory.
        """
        if db_path is None:
            app_dir = Path(__file__).parent.parent
            db_path = app_dir / "data" / "calendar.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calendar entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calendar_entries (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    category TEXT NOT NULL,
                    icon TEXT,
                    description TEXT,
                    is_special INTEGER DEFAULT 0,
                    color TEXT,
                    recurring TEXT,
                    recurring_end_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for fast queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date 
                ON calendar_entries(date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_category 
                ON calendar_entries(category)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_special 
                ON calendar_entries(is_special)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date_category 
                ON calendar_entries(date, category)
            """)
            
            # Weather data table (cached forecasts)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_cache (
                    date TEXT PRIMARY KEY,
                    icon TEXT NOT NULL,
                    temperature_high INTEGER,
                    temperature_low INTEGER,
                    description TEXT,
                    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # App settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def add_entry(self, entry_data: Dict) -> str:
        """Add a new calendar entry.
        
        Args:
            entry_data: Dictionary containing entry fields
            
        Returns:
            Entry ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO calendar_entries 
                (id, title, date, start_time, end_time, category, icon, 
                 description, is_special, color, recurring, recurring_end_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_data['id'],
                entry_data['title'],
                entry_data['date'],
                entry_data.get('start_time'),
                entry_data.get('end_time'),
                entry_data['category'],
                entry_data.get('icon'),
                entry_data.get('description'),
                1 if entry_data.get('is_special') else 0,
                entry_data.get('color'),
                entry_data.get('recurring'),
                entry_data.get('recurring_end_date')
            ))
            
            return entry_data['id']
    
    def get_entries_by_date(self, target_date: date) -> List[Dict]:
        """Get all entries for a specific date.
        
        Args:
            target_date: Date to query
            
        Returns:
            List of entry dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM calendar_entries 
                WHERE date = ?
                ORDER BY start_time
            """, (target_date.isoformat(),))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_entries_by_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """Get all entries within a date range.
        
        Args:
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive)
            
        Returns:
            List of entry dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM calendar_entries 
                WHERE date BETWEEN ? AND ?
                ORDER BY date, start_time
            """, (start_date.isoformat(), end_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_special_events_by_month(self, year: int, month: int) -> List[Dict]:
        """Get special events (birthdays, holidays) for a specific month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            List of special event dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get first and last day of month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            cursor.execute("""
                SELECT * FROM calendar_entries 
                WHERE date >= ? AND date < ? AND is_special = 1
                ORDER BY date
            """, (start_date.isoformat(), end_date.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_weather(self, target_date: date) -> Optional[Dict]:
        """Get cached weather data for a date.
        
        Args:
            target_date: Date to query
            
        Returns:
            Weather dictionary or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM weather_cache 
                WHERE date = ?
            """, (target_date.isoformat(),))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def cache_weather(self, weather_data: Dict):
        """Cache weather data for a date.
        
        Args:
            weather_data: Dictionary with date, icon, temperatures, description
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO weather_cache 
                (date, icon, temperature_high, temperature_low, description, fetched_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                weather_data['date'],
                weather_data['icon'],
                weather_data.get('temperature_high'),
                weather_data.get('temperature_low'),
                weather_data.get('description')
            ))
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT value FROM settings WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            return row['value'] if row else default
    
    def set_setting(self, key: str, value: str):
        """Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
    
    def clear_all_entries(self):
        """Clear all calendar entries (for testing/reset)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM calendar_entries")
    
    def clear_weather_cache(self):
        """Clear all cached weather data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM weather_cache")
