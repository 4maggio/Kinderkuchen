"""
Package initialization for models.
"""

from .calendar_entry import (
    CalendarEntry,
    VALID_CATEGORIES,
    CATEGORY_ICONS,
    CATEGORY_COLORS,
    SPECIAL_CATEGORIES,
    get_default_icon,
    get_default_color,
    is_special_category
)
from .database import CalendarDatabase

__all__ = [
    'CalendarEntry',
    'CalendarDatabase',
    'VALID_CATEGORIES',
    'CATEGORY_ICONS',
    'CATEGORY_COLORS',
    'SPECIAL_CATEGORIES',
    'get_default_icon',
    'get_default_color',
    'is_special_category'
]
