"""
Async NASA API client using httpx.
Wraps: NeoWs, CNEOS Close Approach, HORIZONS (simplified).
"""

import httpx
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from backend.config import get_settings

settings = get_settings()

NASA_BASE = "https://api.nasa.gov"
CNEOS_BASE = "https://ssd-api.jpl.nasa.gov"

_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def close_client():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()


# ── NeoWs Feed ────────────────────────────────────────────────────────────────

async def fetch_neows_feed(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Fetch NASA NeoWs asteroid feed for a date range (max 7 days).
    Defaults to today → today+7.
    """
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=7)

    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "api_key": settings.nasa_api_key,
    }
    client = get_client()
    resp = await client.get(f"{NASA_BASE}/neo/rest/v1/feed", params=params)
    resp.raise_for_status()
    return resp.json()


async def fetch_neo_detail(neo_id: str) -> Dict[str, Any]:
    """Fetch full detail for a single NEO by NASA id."""
    client = get_client()
    resp = await client.get(
        f"{NASA_BASE}/neo/rest/v1/neo/{neo_id}",
        params={"api_key": settings.nasa_api_key},
    )
    resp.raise_for_status()
    return resp.json()


# ── CNEOS Close Approach ──────────────────────────────────────────────────────

async def fetch_close_approaches(
    date_min: str = "now",
    date_max: str = "+60",
    dist_max: str = "10LD",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Fetch close approach data from JPL CNEOS.
    Returns list of approach records.
    """
    params = {
        "date-min": date_min,
        "date-max": date_max,
        "dist-max": dist_max,
        "limit": limit,
        "fullname": True,
    }
    client = get_client()
    resp = await client.get(f"{CNEOS_BASE}/cad.api", params=params)
    resp.raise_for_status()
    data = resp.json()

    # CNEOS returns {"fields": [...], "data": [[...], ...]}
    fields = data.get("fields", [])
    rows = data.get("data", [])
    return [dict(zip(fields, row)) for row in rows]


# ── Parse NeoWs Response ──────────────────────────────────────────────────────

def parse_neows_objects(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Flatten the NeoWs nested response into a list of NEO dicts.
    Each dict contains the NEO fields + soonest close approach.
    """
    result: List[Dict[str, Any]] = []
    near_objects = raw.get("near_earth_objects", {})

    for _date_str, objects in near_objects.items():
        for obj in objects:
            approaches = obj.get("close_approach_data", [])
            soonest = approaches[0] if approaches else {}

            miss_km = float(
                soonest.get("miss_distance", {}).get("kilometers", 0) or 0
            )
            miss_ld = float(
                soonest.get("miss_distance", {}).get("lunar", 0) or 0
            )
            vel_kmps = float(
                soonest.get("relative_velocity", {}).get("kilometers_per_second", 0) or 0
            )

            diam = obj.get("estimated_diameter", {}).get("kilometers", {})
            diam_min = float(diam.get("estimated_diameter_min", 0) or 0)
            diam_max = float(diam.get("estimated_diameter_max", 0) or 0)

            result.append({
                "id": obj["id"],
                "name": obj.get("name", ""),
                "designation": obj.get("designation", ""),
                "is_potentially_hazardous": obj.get(
                    "is_potentially_hazardous_asteroid", False
                ),
                "absolute_magnitude": float(
                    obj.get("absolute_magnitude_h", 0) or 0
                ),
                "estimated_diameter_min_km": diam_min,
                "estimated_diameter_max_km": diam_max,
                "nasa_jpl_url": obj.get("nasa_jpl_url", ""),
                "approach_date": soonest.get("close_approach_date", ""),
                "miss_distance_km": miss_km,
                "miss_distance_ld": miss_ld,
                "relative_velocity_kmps": vel_kmps,
                "semi_major_axis": obj.get("orbital_data", {}).get("semi_major_axis"),
                "eccentricity": obj.get("orbital_data", {}).get("eccentricity"),
                "inclination": obj.get("orbital_data", {}).get("inclination"),
                "raan": obj.get("orbital_data", {}).get("ascending_node_longitude"),
                "arg_perihelion": obj.get("orbital_data", {}).get("perihelion_argument"),
                "mean_anomaly": obj.get("orbital_data", {}).get("mean_anomaly"),
            })

    return result
