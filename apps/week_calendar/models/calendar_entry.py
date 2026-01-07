"""
Calendar entry data model.

Represents a single calendar event with validation and utility methods.
"""

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional
import uuid


@dataclass
class CalendarEntry:
    """Represents a calendar event/entry."""
    
    title: str
    entry_date: date
    category: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    is_special: bool = False
    color: Optional[str] = None
    recurring: Optional[str] = None  # "daily", "weekly", "monthly", or None
    recurring_end_date: Optional[date] = None
    
    def __post_init__(self):
        """Validate entry data after initialization."""
        if not self.title:
            raise ValueError("Title cannot be empty")
        
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {self.category}")
        
        if self.recurring and self.recurring not in VALID_RECURRING_PATTERNS:
            raise ValueError(f"Invalid recurring pattern: {self.recurring}")
        
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("End time must be after start time")
    
    def to_dict(self) -> dict:
        """Convert entry to dictionary for database storage.
        
        Returns:
            Dictionary representation of entry
        """
        return {
            'id': self.id,
            'title': self.title,
            'date': self.entry_date.isoformat(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'category': self.category,
            'icon': self.icon,
            'description': self.description,
            'is_special': self.is_special,
            'color': self.color,
            'recurring': self.recurring,
            'recurring_end_date': self.recurring_end_date.isoformat() if self.recurring_end_date else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CalendarEntry':
        """Create entry from dictionary (e.g., from database).
        
        Args:
            data: Dictionary with entry fields
            
        Returns:
            CalendarEntry instance
        """
        # Convert ISO strings back to date/time objects
        entry_date = date.fromisoformat(data['date'])
        start_time = time.fromisoformat(data['start_time']) if data.get('start_time') else None
        end_time = time.fromisoformat(data['end_time']) if data.get('end_time') else None
        recurring_end_date = date.fromisoformat(data['recurring_end_date']) if data.get('recurring_end_date') else None
        
        return cls(
            id=data['id'],
            title=data['title'],
            date=entry_date,
            start_time=start_time,
            end_time=end_time,
            category=data['category'],
            icon=data.get('icon'),
            description=data.get('description'),
            is_special=bool(data.get('is_special', 0)),
            color=data.get('color'),
            recurring=data.get('recurring'),
            recurring_end_date=recurring_end_date
        )
    
    def get_time_display(self) -> str:
        """Get formatted time string for display.
        
        Returns:
            Formatted time string (e.g., "3:00 PM" or "3:00 PM - 4:30 PM")
        """
        if not self.start_time:
            return "All day"
        
        start_str = self.start_time.strftime("%I:%M %p").lstrip('0')
        
        if self.end_time:
            end_str = self.end_time.strftime("%I:%M %p").lstrip('0')
            return f"{start_str} - {end_str}"
        
        return start_str
    
    def is_all_day(self) -> bool:
        """Check if this is an all-day event.
        
        Returns:
            True if no specific time is set
        """
        return self.start_time is None


# Category definitions (matches Outlook categories)
VALID_CATEGORIES = [
    "School",
    "Sports",
    "Music",
    "Appointments",
    "Birthday",
    "Holiday",
    "Vacation",
    "Home",
    "Other"
]

# Recurring pattern options
VALID_RECURRING_PATTERNS = [
    "daily",
    "weekly",
    "monthly"
]

# Default icons for each category
CATEGORY_ICONS = {
    "School": "school.png",
    "Sports": "sports.png",
    "Music": "music.png",
    "Appointments": "appointment.png",
    "Birthday": "birthday.png",
    "Holiday": "holiday.png",
    "Vacation": "vacation.png",
    "Home": "home.png",
    "Other": "other.png"
}

# Default colors for each category
CATEGORY_COLORS = {
    "School": "#4A90E2",     # Blue
    "Sports": "#E74C3C",     # Red
    "Music": "#2ECC71",      # Green
    "Appointments": "#F39C12",  # Yellow/Orange
    "Birthday": "#9B59B6",   # Purple
    "Holiday": "#E67E22",    # Orange
    "Vacation": "#1ABC9C",   # Teal
    "Home": "#95A5A6",       # Gray
    "Other": "#34495E"       # Dark Gray
}

# Special event categories (shown in year view)
SPECIAL_CATEGORIES = ["Birthday", "Holiday", "Vacation"]


def get_default_icon(category: str) -> str:
    """Get default icon filename for a category.
    
    Args:
        category: Category name
        
    Returns:
        Icon filename
    """
    return CATEGORY_ICONS.get(category, "other.png")


def get_default_color(category: str) -> str:
    """Get default color for a category.
    
    Args:
        category: Category name
        
    Returns:
        Color hex code
    """
    return CATEGORY_COLORS.get(category, "#34495E")


def is_special_category(category: str) -> bool:
    """Check if category should appear in year view.
    
    Args:
        category: Category name
        
    Returns:
        True if this is a special event category
    """
    return category in SPECIAL_CATEGORIES
