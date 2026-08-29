"""Thin NWS client used by the Watch tool.

Adapted (not imported) from Doc Weather's NWS helpers in
Decentralized-Weather-AI-Platform-V-2-0/backend/api/nws_integration.py
as of 2026-08-24. See docs/DISCLOSURE.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import requests

NWS_BASE = "https://api.weather.gov"
USER_AGENT = (
    "WFAD/1.0 (https://github.com/Scrum723/WFAD; "
    "Watch-Forecast-Alert-Disseminate contest agent)"
)
TIMEOUT = 20

# Western New York defaults plus a few national anchors for demos.
KNOWN_POINTS: dict[str, tuple[float, float]] = {
    "rochester, ny": (43.1566, -77.6088),
    "rochester": (43.1566, -77.6088),
    "buffalo, ny": (42.8864, -78.8784),
    "buffalo": (42.8864, -78.8784),
    "syracuse, ny": (43.0481, -76.1474),
    "jamestown, ny": (42.0970, -79.2353),
    "erie, pa": (42.1292, -80.0851),
    "new york, ny": (40.7128, -74.0060),
    "new york": (40.7128, -74.0060),
}

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json, application/ld+json",
    }
)


def _qv(value_obj: Any) -> float | None:
    if not isinstance(value_obj, dict):
        return None
    val = value_obj.get("value")
    return float(val) if val is not None else None


def _qv_unit(value_obj: Any) -> tuple[float | None, str | None]:
    if not isinstance(value_obj, dict):
        return None, None
    val = value_obj.get("value")
    return (float(val) if val is not None else None), value_obj.get("unitCode")


def _c_to_f(c: float | None) -> float | None:
    if c is None:
        return None
    return round(c * 9 / 5 + 32, 1)


def _to_mph(value: float | None, unit_code: str | None) -> float | None:
    """NWS wind is usually km/h (wmoUnit:km_h-1), not m/s."""
    if value is None:
        return None
    unit = (unit_code or "").lower()
    if "km_h" in unit or "km/h" in unit:
        return round(value * 0.621371, 1)
    if "m_s" in unit or "m/s" in unit:
        return round(value * 2.23694, 1)
    if "mi_h" in unit or "mile" in unit:
        return round(float(value), 1)
    if "kn" in unit:
        return round(value * 1.15078, 1)
    return round(value * 0.621371, 1)


def _geocode(city: str) -> tuple[float, float, str]:
    key = city.strip().lower()
    if key in KNOWN_POINTS:
        lat, lon = KNOWN_POINTS[key]
        return lat, lon, "known_point"
    params = {
        "address": city,
        "benchmark": "Public_AR_Current",
        "format": "json",
    }
    try:
        resp = requests.get(
            "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress",
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        matches = (
            resp.json()
            .get("result", {})
            .get("addressMatches", [])
        )
        if matches:
            coords = matches[0]["coordinates"]
            return float(coords["y"]), float(coords["x"]), "census_geocoder"
    except Exception as exc:  # noqa: BLE001 — contest client; return a labeled failure
        return 43.1566, -77.6088, f"geocode_failed:{exc};fell_back_rochester"
    return 43.1566, -77.6088, "unknown_city_fell_back_rochester"


def _nws_get(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = SESSION.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _parse_alert(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties") or {}
    return {
        "id": props.get("id") or feature.get("id"),
        "event": props.get("event"),
        "headline": props.get("headline"),
        "severity": props.get("severity"),
        "urgency": props.get("urgency"),
        "certainty": props.get("certainty"),
        "area": props.get("areaDesc"),
        "effective": props.get("effective"),
        "expires": props.get("expires"),
        "instruction": (props.get("instruction") or "")[:500],
        "description": (props.get("description") or "")[:800],
        "sender": props.get("senderName"),
    }


def watch_conditions(
    city: str = "Rochester, NY",
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> dict:
    """Pull weather products. Prefers Doc's neural-network snapshot; NWS if Doc is down.

    Args:
        city: City name, for example "Rochester, NY". Used when lat/lon are 0.
        latitude: Optional latitude. Non-zero values take precedence over city.
        longitude: Optional longitude. Non-zero values take precedence over city.

    Returns:
        A dict with status, location, hazards, observations, forecast periods,
        and any per-step failures.
    """
    failures: list[str] = []
    source = "latlon"
    if latitude and longitude:
        lat, lon = float(latitude), float(longitude)
    else:
        lat, lon, source = _geocode(city or "Rochester, NY")

    try:
        from .doc_client import fetch_snapshot, snapshot_to_watch

        snap = fetch_snapshot(lat, lon, city or "Rochester, NY")
        watch = snapshot_to_watch(snap, city or "Rochester, NY", lat, lon)
        watch["geocode_source"] = source
        watch["doc_ok"] = True
        return watch
    except Exception as exc:  # noqa: BLE001
        failures.append(f"doc_snapshot:{exc}")

    point: dict[str, Any] = {}
    office = None
    forecast_url = None
    stations_url = None
    try:
        point = _nws_get(f"{NWS_BASE}/points/{lat:.4f},{lon:.4f}")
        props = point.get("properties") or {}
        office = props.get("cwa")
        forecast_url = props.get("forecast")
        stations_url = props.get("observationStations")
        relative = props.get("relativeLocation", {}).get("properties", {})
        city_name = relative.get("city") or city
        state_name = relative.get("state") or ""
    except Exception as exc:  # noqa: BLE001
        failures.append(f"points:{exc}")
        city_name, state_name = city, ""

    hazards: list[dict[str, Any]] = []
    try:
        alerts = _nws_get(
            f"{NWS_BASE}/alerts/active",
            params={"point": f"{lat},{lon}", "status": "actual"},
        )
        hazards = [_parse_alert(f) for f in alerts.get("features", [])]
    except Exception as exc:  # noqa: BLE001
        failures.append(f"alerts:{exc}")

    observation: dict[str, Any] = {}
    station_id = None
    try:
        if stations_url:
            stations = _nws_get(stations_url)
            features = stations.get("features") or []
            if features:
                station_id = features[0].get("properties", {}).get("stationIdentifier")
        if station_id:
            obs = _nws_get(f"{NWS_BASE}/stations/{station_id}/observations/latest")
            oprops = obs.get("properties") or {}
            temp_c = _qv(oprops.get("temperature"))
            wind_val, wind_unit = _qv_unit(oprops.get("windSpeed"))
            observation = {
                "station_id": station_id,
                "timestamp": oprops.get("timestamp"),
                "text": oprops.get("textDescription"),
                "temperature_c": temp_c,
                "temperature_f": _c_to_f(temp_c),
                "wind_mph": _to_mph(wind_val, wind_unit),
                "wind_unit_source": wind_unit,
                "relative_humidity": _qv(oprops.get("relativeHumidity")),
                "raw_metar": oprops.get("rawMessage"),
            }
    except Exception as exc:  # noqa: BLE001
        failures.append(f"observation:{exc}")

    periods: list[dict[str, Any]] = []
    try:
        if forecast_url:
            fcst = _nws_get(forecast_url)
            for period in (fcst.get("properties") or {}).get("periods", [])[:4]:
                periods.append(
                    {
                        "name": period.get("name"),
                        "start": period.get("startTime"),
                        "temperature": period.get("temperature"),
                        "unit": period.get("temperatureUnit"),
                        "wind": f"{period.get('windSpeed')} {period.get('windDirection')}".strip(),
                        "forecast": period.get("shortForecast"),
                        "detailed": (period.get("detailedForecast") or "")[:400],
                    }
                )
    except Exception as exc:  # noqa: BLE001
        failures.append(f"forecast:{exc}")

    status = "success" if not failures else ("partial" if (hazards or observation or periods) else "error")
    return {
        "status": status,
        "source": "api.weather.gov",
        "geocode_source": source,
        "location": {
            "city": city_name,
            "state": state_name,
            "lat": lat,
            "lon": lon,
            "cwa": office,
            "station_id": station_id,
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "hazards": hazards,
        "observation": observation,
        "forecast_periods": periods,
        "failures": failures,
    }


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "Rochester, NY"
    print(json.dumps(watch_conditions(city=target), indent=2))
