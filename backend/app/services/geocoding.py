"""Address geocoding and distance calculation service for Transport.

Provides address-first resolution: maps human-readable addresses to coordinates
(latitude, longitude) and computes Haversine distances between student locations
and bus route stops.
"""

import math
import re
import urllib.parse
import urllib.request
import json
import logging

logger = logging.getLogger(__name__)

# Base location for Sunrise Public School (Lucknow / Uttar Pradesh territory)
BASE_LATITUDE = 26.8500
BASE_LONGITUDE = 80.9800

# Landmark & Area registry with verified coordinates
KNOWN_COORDINATES: dict[str, tuple[float, float, str]] = {
    # Lucknow (Primary territory for demo and test seeds)
    "vibhuti khand": (26.8722, 80.9994, "Vibhuti Khand, Gomti Nagar, Lucknow"),
    "fun republic": (26.8530, 80.9782, "Fun Republic Mall, Lohia Path, Gomti Nagar, Lucknow"),
    "patrakarpuram": (26.8491, 80.9950, "Patrakarpuram Crossing, Gomti Nagar, Lucknow"),
    "vinay khand": (26.8524, 81.0112, "Vinay Khand, Gomti Nagar, Lucknow"),
    "lohia park": (26.8540, 80.9820, "Dr. Ram Manohar Lohia Park, Gomti Nagar, Lucknow"),
    "vikas khand": (26.8480, 81.0180, "Vikas Khand, Gomti Nagar, Lucknow"),
    "ambedkar park": (26.8470, 80.9780, "Ambedkar Memorial Park, Vipin Khand, Lucknow"),
    "krishna nagar": (26.7924, 80.8932, "Krishna Nagar, Kanpur Road, Lucknow"),
    "sadar bazaar": (26.8220, 80.9320, "Sadar Bazaar, Cantonment, Lucknow"),
    "alambagh": (26.8150, 80.9080, "Alambagh Bus Station / Terminal, Lucknow"),
    "kanpur road": (26.7640, 80.8800, "Kanpur Road, Sector B, Lucknow"),
    "phoenix palassio": (26.8120, 81.0200, "Phoenix Palassio, Sector 7, Gomti Nagar Extension, Lucknow"),
    "hazratganj": (26.8467, 80.9462, "Hazratganj, Lucknow"),
    "charbagh": (26.8320, 80.9220, "Charbagh, Lucknow"),
    "indira nagar": (26.8850, 80.9900, "Indira Nagar, Lucknow"),
    "jankipuram": (26.9200, 80.9500, "Jankipuram, Lucknow"),
    "ashiyana": (26.7880, 80.9120, "Ashiyana, Lucknow"),
    "chinhat": (26.8800, 81.0400, "Chinhat, Lucknow"),
    "mahanagar": (26.8780, 80.9560, "Mahanagar, Lucknow"),
    "gomti nagar": (26.8500, 80.9950, "Gomti Nagar, Lucknow"),
    "rajajipuram": (26.8350, 80.8850, "Rajajipuram, Lucknow"),
    "chowk": (26.8680, 80.9050, "Chowk, Old City, Lucknow"),

    # Delhi NCR / Satellite Campuses
    "indirapuram": (28.6360, 77.3680, "Indirapuram, Ghaziabad, UP"),
    "sector 62": (28.6280, 77.3650, "Sector 62, Noida, UP"),
    "vaishali": (28.6480, 77.3400, "Vaishali, Ghaziabad, UP"),
    "vasundhara": (28.6600, 77.3750, "Vasundhara, Ghaziabad, UP"),
    "kaushambi": (28.6400, 77.3200, "Kaushambi, Ghaziabad, UP"),
    "noida city centre": (28.5740, 77.3560, "Noida City Centre, Sector 32, Noida"),
    "hathi park": (26.8570, 80.9850, "Hathi Park, Lucknow"),
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth in kilometers."""
    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 2)


def geocode_address(raw_address: str | None) -> dict:
    """Resolve a human-readable address into geographical coordinates (lat, lon).

    Returns a dict with:
      - address: formatted or original address
      - latitude: float
      - longitude: float
      - is_approximate: bool
    """
    if not raw_address or not raw_address.strip():
        return {
            "address": "",
            "latitude": BASE_LATITUDE,
            "longitude": BASE_LONGITUDE,
            "is_approximate": True,
        }

    clean_text = raw_address.strip()
    norm = clean_text.lower()

    # 1. Match against known territory landmarks
    for key, (lat, lon, formatted) in KNOWN_COORDINATES.items():
        if key in norm:
            return {
                "address": clean_text,
                "latitude": lat,
                "longitude": lon,
                "is_approximate": False,
            }

    # 2. Try online OpenStreetMap Nominatim with a short timeout if possible
    try:
        query = urllib.parse.quote(f"{clean_text}, Lucknow, India")
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}&limit=1"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Sunrise-School-ERP-Transport/1.0"},
        )
        with urllib.request.urlopen(req, timeout=1.5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data and len(data) > 0:
                    item = data[0]
                    return {
                        "address": clean_text,
                        "latitude": round(float(item["lat"]), 4),
                        "longitude": round(float(item["lon"]), 4),
                        "is_approximate": False,
                    }
    except Exception as exc:
        logger.debug("Online geocoding skipped or timed out: %s", exc)

    # 3. Deterministic territorial offset fallback so coordinates are always valid
    h = abs(hash(norm))
    lat_offset = ((h % 100) - 50) * 0.0008
    lon_offset = (((h // 100) % 100) - 50) * 0.0008

    return {
        "address": clean_text,
        "latitude": round(BASE_LATITUDE + lat_offset, 4),
        "longitude": round(BASE_LONGITUDE + lon_offset, 4),
        "is_approximate": True,
    }
