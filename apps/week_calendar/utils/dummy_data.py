"""
Dummy data generator for development and testing.

Creates realistic school schedule and sample events.
"""

from datetime import date, time, timedelta
from typing import List
import uuid

from models.calendar_entry import CalendarEntry, get_default_icon, get_default_color


def generate_dummy_data(start_date: date = None, weeks: int = 4) -> List[CalendarEntry]:
    """Generate dummy calendar entries for testing.
    
    Args:
        start_date: Start date for generating entries (defaults to today)
        weeks: Number of weeks to generate (default: 4)
        
    Returns:
        List of CalendarEntry objects
    """
    if start_date is None:
        start_date = date.today()
    
    entries = []
    
    # Generate entries for each week
    for week in range(weeks):
        week_start = start_date + timedelta(weeks=week)
        
        # Find Monday of this week
        monday = week_start - timedelta(days=week_start.weekday())
        
        # School days (Monday - Friday)
        for day in range(5):  # 0=Monday, 4=Friday
            current_date = monday + timedelta(days=day)
            
            # School (recurring Monday-Friday)
            entries.append(CalendarEntry(
                title="School",
                date=current_date,
                start_time=time(8, 0),
                end_time=time(15, 0),
                category="School",
                icon=get_default_icon("School"),
                color=get_default_color("School"),
                description="Regular school day"
            ))
        
        # Monday activities
        monday_date = monday
        entries.append(CalendarEntry(
            title="Soccer Practice",
            date=monday_date,
            start_time=time(15, 30),
            end_time=time(17, 0),
            category="Sports",
            icon=get_default_icon("Sports"),
            color=get_default_color("Sports"),
            description="Bring cleats and water bottle"
        ))
        entries.append(CalendarEntry(
            title="Piano Lesson",
            date=monday_date,
            start_time=time(17, 30),
            end_time=time(18, 30),
            category="Music",
            icon=get_default_icon("Music"),
            color=get_default_color("Music"),
            description="Practice scales"
        ))
        
        # Wednesday activities
        wednesday_date = monday + timedelta(days=2)
        entries.append(CalendarEntry(
            title="Soccer Practice",
            date=wednesday_date,
            start_time=time(15, 30),
            end_time=time(17, 0),
            category="Sports",
            icon=get_default_icon("Sports"),
            color=get_default_color("Sports"),
            description="Bring cleats and water bottle"
        ))
        entries.append(CalendarEntry(
            title="Piano Lesson",
            date=wednesday_date,
            start_time=time(17, 30),
            end_time=time(18, 30),
            category="Music",
            icon=get_default_icon("Music"),
            color=get_default_color("Music"),
            description="Practice scales"
        ))
        
        # Thursday: Doctor appointment (only first week)
        if week == 1:
            thursday_date = monday + timedelta(days=3)
            entries.append(CalendarEntry(
                title="Doctor Checkup",
                date=thursday_date,
                start_time=time(16, 0),
                end_time=time(17, 0),
                category="Appointments",
                icon=get_default_icon("Appointments"),
                color=get_default_color("Appointments"),
                description="Annual checkup with Dr. Smith"
            ))
        
        # Friday activities
        friday_date = monday + timedelta(days=4)
        entries.append(CalendarEntry(
            title="Soccer Practice",
            date=friday_date,
            start_time=time(15, 30),
            end_time=time(17, 0),
            category="Sports",
            icon=get_default_icon("Sports"),
            color=get_default_color("Sports"),
            description="Bring cleats and water bottle"
        ))
        
        # Saturday: Soccer game
        saturday_date = monday + timedelta(days=5)
        entries.append(CalendarEntry(
            title="Soccer Game",
            date=saturday_date,
            start_time=time(10, 0),
            end_time=time(11, 30),
            category="Sports",
            icon=get_default_icon("Sports"),
            color=get_default_color("Sports"),
            description="Home game vs. Blue Team"
        ))
        
        # Saturday: Birthday party (only second week)
        if week == 1:
            entries.append(CalendarEntry(
                title="Emma's Birthday Party",
                date=saturday_date,
                start_time=time(14, 0),
                end_time=time(16, 0),
                category="Birthday",
                icon=get_default_icon("Birthday"),
                color=get_default_color("Birthday"),
                description="Bring present! Party at the park",
                is_special=True
            ))
    
    # Add some special events (birthdays, holidays)
    
    # Birthday - 15 days from start
    birthday_date = start_date + timedelta(days=15)
    entries.append(CalendarEntry(
        title="Dad's Birthday",
        date=birthday_date,
        category="Birthday",
        icon=get_default_icon("Birthday"),
        color=get_default_color("Birthday"),
        description="🎂 Don't forget to make card!",
        is_special=True
    ))
    
    # Holiday - 20 days from start (if within range)
    if weeks >= 3:
        holiday_date = start_date + timedelta(days=20)
        entries.append(CalendarEntry(
            title="School Holiday",
            date=holiday_date,
            category="Holiday",
            icon=get_default_icon("Holiday"),
            color=get_default_color("Holiday"),
            description="No school - woohoo!",
            is_special=True
        ))
    
    return entries


def populate_database_with_dummy_data(database, start_date: date = None, weeks: int = 4):
    """Populate database with dummy data.
    
    Args:
        database: CalendarDatabase instance
        start_date: Start date for generating entries
        weeks: Number of weeks to generate
    """
    entries = generate_dummy_data(start_date, weeks)
    
    for entry in entries:
        database.add_entry(entry.to_dict())
    
    print(f"Added {len(entries)} dummy calendar entries to database")


def generate_dummy_weather(start_date: date = None, days: int = 14) -> List[dict]:
    """Generate dummy weather data for testing.
    
    Args:
        start_date: Start date (defaults to today)
        days: Number of days to generate (default: 14)
        
    Returns:
        List of weather dictionaries
    """
    if start_date is None:
        start_date = date.today()
    
    weather_icons = ["sunny", "cloudy", "rainy", "partly_cloudy", "sunny"]
    weather_data = []
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        icon = weather_icons[day % len(weather_icons)]
        
        weather_data.append({
            'date': current_date.isoformat(),
            'icon': f"{icon}.png",
            'temperature_high': 65 + (day % 15),
            'temperature_low': 50 + (day % 10),
            'description': icon.replace('_', ' ').title()
        })
    
    return weather_data


def populate_weather_cache(database, start_date: date = None, days: int = 14):
    """Populate database weather cache with dummy data.
    
    Args:
        database: CalendarDatabase instance
        start_date: Start date
        days: Number of days to cache
    """
    weather_data = generate_dummy_weather(start_date, days)
    
    for weather in weather_data:
        database.cache_weather(weather)
    
    print(f"Added {len(weather_data)} days of dummy weather data to cache")


if __name__ == "__main__":
    # Test data generation
    from models.database import CalendarDatabase
    
    db = CalendarDatabase()
    db.clear_all_entries()
    db.clear_weather_cache()
    
    populate_database_with_dummy_data(db, weeks=4)
    populate_weather_cache(db, days=14)
    
    print("\nDummy data generation complete!")
    print("Database location:", db.db_path)
