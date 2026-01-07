"""
Weather API integration using Open-Meteo.

Open-Meteo provides free weather forecasts without requiring an API key.
Documentation: https://open-meteo.com/
"""

import requests
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional


class WeatherAPI:
    """Weather data fetcher using Open-Meteo API."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    def __init__(self, latitude: float = 51.5074, longitude: float = -0.1278, timezone: str = "Europe/London"):
        """Initialize weather API client.
        
        Args:
            latitude: Location latitude (default: London)
            longitude: Location longitude (default: London)
            timezone: Timezone string (default: Europe/London)
        """
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
    
    def fetch_forecast(self, days: int = 7) -> List[Dict]:
        """Fetch weather forecast for upcoming days.
        
        Args:
            days: Number of days to forecast (max 16)
            
        Returns:
            List of weather dictionaries with date, icon, temperatures, description
        """
        try:
            params = {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'daily': 'temperature_2m_max,temperature_2m_min,weathercode',
                'timezone': self.timezone,
                'forecast_days': min(days, 16)  # Open-Meteo supports up to 16 days
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_forecast(data)
            
        except requests.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return self._get_fallback_forecast(days)
    
    def _parse_forecast(self, data: Dict) -> List[Dict]:
        """Parse Open-Meteo API response into our format.
        
        Args:
            data: API response JSON
            
        Returns:
            List of weather dictionaries
        """
        forecasts = []
        
        daily = data.get('daily', {})
        dates = daily.get('time', [])
        temps_max = daily.get('temperature_2m_max', [])
        temps_min = daily.get('temperature_2m_min', [])
        weather_codes = daily.get('weathercode', [])
        
        for i, date_str in enumerate(dates):
            icon, description = self._get_icon_and_description(weather_codes[i])
            
            forecasts.append({
                'date': date_str,
                'icon': icon,
                'temperature_high': int(temps_max[i]) if i < len(temps_max) else None,
                'temperature_low': int(temps_min[i]) if i < len(temps_min) else None,
                'description': description
            })
        
        return forecasts
    
    def _get_icon_and_description(self, weather_code: int) -> tuple:
        """Map WMO weather code to icon and description.
        
        WMO Weather interpretation codes:
        0: Clear sky
        1-3: Mainly clear, partly cloudy, overcast
        45-48: Fog
        51-55: Drizzle
        61-65: Rain
        71-75: Snow
        80-82: Rain showers
        95-99: Thunderstorm
        
        Args:
            weather_code: WMO weather code
            
        Returns:
            Tuple of (icon_filename, description)
        """
        if weather_code == 0:
            return "sunny.png", "Clear"
        elif weather_code in [1, 2]:
            return "partly_cloudy.png", "Partly Cloudy"
        elif weather_code == 3:
            return "cloudy.png", "Cloudy"
        elif weather_code in [45, 48]:
            return "fog.png", "Foggy"
        elif weather_code in [51, 53, 55]:
            return "drizzle.png", "Drizzle"
        elif weather_code in [61, 63, 65, 80, 81, 82]:
            return "rainy.png", "Rainy"
        elif weather_code in [71, 73, 75, 77]:
            return "snowy.png", "Snowy"
        elif weather_code in [95, 96, 99]:
            return "stormy.png", "Stormy"
        else:
            return "cloudy.png", "Cloudy"
    
    def _get_fallback_forecast(self, days: int) -> List[Dict]:
        """Generate fallback weather data when API is unavailable.
        
        Args:
            days: Number of days to generate
            
        Returns:
            List of fallback weather dictionaries
        """
        print("Using fallback weather data")
        
        fallback_patterns = [
            ("sunny.png", "Clear", 72, 58),
            ("partly_cloudy.png", "Partly Cloudy", 68, 55),
            ("cloudy.png", "Cloudy", 65, 52),
            ("rainy.png", "Rainy", 60, 50)
        ]
        
        forecasts = []
        today = date.today()
        
        for i in range(days):
            current_date = today + timedelta(days=i)
            icon, desc, temp_high, temp_low = fallback_patterns[i % len(fallback_patterns)]
            
            forecasts.append({
                'date': current_date.isoformat(),
                'icon': icon,
                'temperature_high': temp_high,
                'temperature_low': temp_low,
                'description': desc
            })
        
        return forecasts
    
    def set_location(self, latitude: float, longitude: float, timezone: str = None):
        """Update location for weather forecasts.
        
        Args:
            latitude: New latitude
            longitude: New longitude
            timezone: New timezone (optional)
        """
        self.latitude = latitude
        self.longitude = longitude
        if timezone:
            self.timezone = timezone
    
    @staticmethod
    def get_location_coordinates(city_name: str) -> Optional[tuple]:
        """Get coordinates for a city (using Open-Meteo geocoding).
        
        Args:
            city_name: Name of the city
            
        Returns:
            Tuple of (latitude, longitude, timezone) or None if not found
        """
        try:
            url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                'name': city_name,
                'count': 1,
                'language': 'en',
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                result = results[0]
                return (
                    result['latitude'],
                    result['longitude'],
                    result.get('timezone', 'Europe/London')
                )
            
            return None
            
        except requests.RequestException as e:
            print(f"Error geocoding city: {e}")
            return None
    
    @staticmethod
    def search_locations(query: str, count: int = 10) -> List[Dict]:
        """Search for locations by name (using Open-Meteo geocoding).
        
        Args:
            query: Search query (city name)
            count: Maximum number of results
            
        Returns:
            List of location dictionaries with name, country, latitude, longitude, timezone
        """
        try:
            url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                'name': query,
                'count': count,
                'language': 'en',
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            locations = []
            for result in results:
                # Build display name with country and admin region
                name_parts = [result['name']]
                if result.get('admin1'):
                    name_parts.append(result['admin1'])
                name_parts.append(result['country'])
                display_name = ', '.join(name_parts)
                
                locations.append({
                    'display_name': display_name,
                    'name': result['name'],
                    'country': result['country'],
                    'latitude': result['latitude'],
                    'longitude': result['longitude'],
                    'timezone': result.get('timezone', 'Europe/London')
                })
            
            return locations
            
        except requests.RequestException as e:
            print(f"Error searching locations: {e}")
            return []


def fetch_and_cache_weather(database, weather_api: WeatherAPI, days: int = 14):
    """Fetch weather forecast and cache it in database.
    
    Args:
        database: CalendarDatabase instance
        weather_api: WeatherAPI instance
        days: Number of days to fetch
    """
    forecasts = weather_api.fetch_forecast(days)
    
    for forecast in forecasts:
        database.cache_weather(forecast)
    
    print(f"Cached {len(forecasts)} days of weather data")


if __name__ == "__main__":
    # Test the weather API
    print("Testing Open-Meteo weather API...")
    
    # Default location (London)
    api = WeatherAPI()
    forecasts = api.fetch_forecast(7)
    
    print(f"\nWeather forecast for next 7 days:")
    for forecast in forecasts:
        print(f"  {forecast['date']}: {forecast['description']}, "
              f"High: {forecast['temperature_high']}°F, "
              f"Low: {forecast['temperature_low']}°F, "
              f"Icon: {forecast['icon']}")
    
    # Test geocoding
    print("\nTesting geocoding...")
    coords = WeatherAPI.get_location_coordinates("Berlin")
    if coords:
        print(f"Berlin coordinates: {coords}")
        
        # Get weather for Berlin
        api.set_location(coords[0], coords[1], coords[2])
        berlin_forecasts = api.fetch_forecast(3)
        print(f"\nBerlin weather (3 days):")
        for forecast in berlin_forecasts:
            print(f"  {forecast['date']}: {forecast['description']}")
