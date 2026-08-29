"""HTTP client for Doc Weather products. WFAD does not import the Doc backend.

Doc neural network (14 modules) is the weather source. Live API:
https://weather-agi-production.up.railway.app
"""

from __future__ import annotations

import os
from typing import Any

import requests

DOC_API = os.environ.get(
    "DOC_API_BASE", "https://weather-agi-production.up.railway.app"
).rstrip("/")
TIMEOUT = 25


def fetch_snapshot(lat: float, lon: float, location_name: str = "Rochester, NY") -> dict[str, Any]:
    resp = requests.get(
        f"{DOC_API}/api/public/snapshot",
        params={
            "lat": lat,
            "lon": lon,
            "location_name": location_name,
            "include_agi": "false",
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise RuntimeError("Doc snapshot was not an object")
    return data


def fetch_network_status() -> dict[str, Any]:
    try:
        resp = requests.get(f"{DOC_API}/api/doc/neural-network", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {"raw": data}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error_message": str(exc)}


def snapshot_to_watch(snap: dict[str, Any], city: str, lat: float, lon: float) -> dict[str, Any]:
    """Normalize Doc snapshot into the Watch payload Story desk already uses."""
    current = snap.get("current") or {}
    brief = snap.get("brief") or {}
    loc_name = snap.get("location_name") or city
    periods_in = snap.get("periods") or []
    periods = []
    for period in periods_in[:8]:
        if not isinstance(period, dict):
            continue
        periods.append(
            {
                "name": period.get("name"),
                "start": period.get("startTime"),
                "temperature": period.get("temperature"),
                "unit": period.get("temperatureUnit") or "F",
                "wind": f"{period.get('windSpeed') or ''} {period.get('windDirection') or ''}".strip(),
                "forecast": period.get("shortForecast"),
                "detailed": (period.get("detailedForecast") or "")[:400],
                "pop": period.get("probabilityOfPrecipitation"),
            }
        )
    hazards = []
    for item in (snap.get("alerts") or []) + (snap.get("nearby_zone_alerts") or []):
        if isinstance(item, dict):
            hazards.append(item)
    media = snap.get("media") or {}
    radar = (media.get("radar") or {}) if isinstance(media, dict) else {}
    sat = (media.get("satellite") or {}) if isinstance(media, dict) else {}
    return {
        "status": "success",
        "source": "doc_snapshot",
        "doc_api": DOC_API,
        "geocode_source": "caller",
        "location": {
            "city": loc_name.split(",")[0].strip() if loc_name else city,
            "state": "",
            "lat": lat,
            "lon": lon,
            "cwa": None,
            "station_id": current.get("station_id"),
        },
        "fetched_at": snap.get("generated_at"),
        "hazards": hazards,
        "observation": {
            "station_id": current.get("station_id"),
            "timestamp": current.get("observed_at"),
            "text": current.get("conditions") or brief.get("conditions"),
            "temperature_c": current.get("temperature_c"),
            "temperature_f": current.get("temperature_f") or brief.get("current_temp_f"),
            "wind_mph": current.get("wind_speed_mph") or brief.get("wind_mph"),
            "relative_humidity": current.get("humidity") or brief.get("humidity"),
            "raw_metar": current.get("raw_metar"),
        },
        "forecast_periods": periods,
        "doc_brief": brief,
        "doc_media": {
            "radar_latest": radar.get("site_base_reflectivity")
            or radar.get("us_composite_base_reflectivity"),
            "radar_viewer": radar.get("nws_radar_viewer") or radar.get("nws_viewer"),
            "satellite_geocolor": sat.get("northeast_geocolor") or sat.get("conus_geocolor"),
            "radar_site": (radar.get("nearest_site") or {}).get("site_id"),
        },
        "failures": [],
    }
