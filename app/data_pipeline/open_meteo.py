import httpx
import logging
from typing import Dict, Any
from async_lru import alru_cache

logger = logging.getLogger(__name__)


class OpenMeteoClient:
    """Fetches real-time climate data from Open-Meteo (completely free, no API key)."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    _client: httpx.AsyncClient = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(timeout=10.0)
        return cls._client

    @staticmethod
    @alru_cache(maxsize=128)
    async def get_environmental_data(lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetches comprehensive climate data for SDG 13 extreme event analysis.
        Includes: temperature, humidity, precipitation, wind, pressure, soil moisture.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ",".join([
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "precipitation",
                "rain",
                "surface_pressure",
                "wind_speed_10m",
                "wind_gusts_10m",
                "soil_moisture_0_to_1cm",
                "weather_code",
            ]),
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
            ]),
            "forecast_days": 7,
            "timezone": "auto",
        }

        client = OpenMeteoClient.get_client()
        try:
            response = await client.get(
                OpenMeteoClient.BASE_URL, params=params
            )
            response.raise_for_status()
            data = response.json()
            current = data.get("current", {})
            daily = data.get("daily", {})

            # Extract daily forecasts (today + 2 days)
            precip_daily = daily.get("precipitation_sum", [0.0])
            temp_max_daily = daily.get("temperature_2m_max", [30.0])
            temp_min_daily = daily.get("temperature_2m_min", [20.0])
            wind_max_daily = daily.get("wind_speed_10m_max", [10.0])
            gust_max_daily = daily.get("wind_gusts_10m_max", [20.0])

            return {
                # Current conditions
                "temperature_c": current.get("temperature_2m", 25.0),
                "apparent_temperature_c": current.get("apparent_temperature", 25.0),
                "precipitation_mm": current.get("precipitation", 0.0),
                "rain_mm": current.get("rain", 0.0),
                "soil_moisture": current.get("soil_moisture_0_to_1cm", 0.2),
                "humidity": current.get("relative_humidity_2m", 50.0),
                "surface_pressure_hpa": current.get("surface_pressure", 1013.0),
                "wind_speed_kmh": current.get("wind_speed_10m", 10.0),
                "wind_gusts_kmh": current.get("wind_gusts_10m", 20.0),
                "weather_code": current.get("weather_code", 0),
                "elevation": data.get("elevation", 100.0),
                # Daily forecasts
                "precip_today_mm": precip_daily[0] if precip_daily else 0.0,
                "precip_forecast_mm": precip_daily,
                "temp_max_today_c": temp_max_daily[0] if temp_max_daily else 30.0,
                "temp_min_today_c": temp_min_daily[0] if temp_min_daily else 20.0,
                "temp_max_forecast_c": temp_max_daily,
                "wind_max_today_kmh": wind_max_daily[0] if wind_max_daily else 10.0,
                "gust_max_today_kmh": gust_max_daily[0] if gust_max_daily else 20.0,
            }
        except Exception as e:
            logger.error(f"Failed to fetch climate data: {e}")
            # Fallback data to prevent system crash
            return {
                "temperature_c": 25.0,
                "apparent_temperature_c": 25.0,
                "precipitation_mm": 0.0,
                "rain_mm": 0.0,
                "soil_moisture": 0.2,
                "humidity": 50.0,
                "surface_pressure_hpa": 1013.0,
                "wind_speed_kmh": 10.0,
                "wind_gusts_kmh": 20.0,
                "weather_code": 0,
                "elevation": 100.0,
                "precip_today_mm": 0.0,
                "precip_forecast_mm": [0.0],
                "temp_max_today_c": 30.0,
                "temp_min_today_c": 20.0,
                "temp_max_forecast_c": [30.0],
                "wind_max_today_kmh": 10.0,
                "gust_max_today_kmh": 20.0,
            }