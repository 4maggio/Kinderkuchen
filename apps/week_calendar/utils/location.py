"""
Utility to get location from IP address for automatic weather location.
"""

import requests
from typing import Optional, Tuple


def get_location_from_ip() -> Optional[Tuple[float, float, str, str]]:
    """Get location coordinates from IP address.
    
    Uses ip-api.com free service (no API key required).
    Limit: 45 requests per minute from an IP address.
    
    Returns:
        Tuple of (latitude, longitude, city_name, timezone) or None on failure
    """
    try:
        # Use ip-api.com - free, no API key needed
        url = "http://ip-api.com/json/?fields=status,lat,lon,city,timezone"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'success':
            return (
                data['lat'],
                data['lon'],
                data['city'],
                data['timezone']
            )
        
        return None
        
    except requests.RequestException as e:
        print(f"Error getting location from IP: {e}")
        return None


def get_timezone_for_coordinates(latitude: float, longitude: float) -> str:
    """Get timezone for given coordinates using Open-Meteo.
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        Timezone string (e.g., "Europe/London") or default
    """
    try:
        # Use Open-Meteo's timezone endpoint
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'timezone': 'auto'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data.get('timezone', 'Europe/London')
        
    except requests.RequestException as e:
        print(f"Error getting timezone: {e}")
        return "Europe/London"


if __name__ == "__main__":
    # Test IP location detection
    print("Testing IP-based location detection...")
    
    location = get_location_from_ip()
    if location:
        lat, lon, city, tz = location
        print(f"Detected location: {city}")
        print(f"Coordinates: {lat}, {lon}")
        print(f"Timezone: {tz}")
    else:
        print("Failed to detect location")
