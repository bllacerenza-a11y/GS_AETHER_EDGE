import httpx
import logging
from typing import Optional
from async_lru import alru_cache

logger = logging.getLogger(__name__)


class Geocoder:
    """Converts region/city names to coordinates using OpenStreetMap Nominatim (free)."""

    BASE_URL = "https://nominatim.openstreetmap.org/search"
    _client: httpx.AsyncClient = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(timeout=10.0)
        return cls._client

    @staticmethod
    @alru_cache(maxsize=128)
    async def geocode(region_name: str) -> Optional[dict]:
        """
        Converts a region name (e.g. 'São Paulo', 'Rio de Janeiro') to lat/lon.
        Returns dict with latitude, longitude, and display_name, or None if not found.
        """
        params = {
            "q": region_name,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {
            "User-Agent": "AETHER-GeoAI/1.0 (climate-risk-analysis)"
        }

        client = Geocoder.get_client()
        try:
            response = await client.get(
                Geocoder.BASE_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            results = response.json()

            if not results:
                return None

            place = results[0]
            return {
                "latitude": float(place["lat"]),
                "longitude": float(place["lon"]),
                "display_name": place.get("display_name", region_name),
            }
        except Exception as e:
            logger.error(f"Geocoding failed for '{region_name}': {e}")
            return None
