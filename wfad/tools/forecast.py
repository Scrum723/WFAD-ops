"""Briefing formatter. The Gemini model may also write prose; this tool
keeps the package grounded in Watch output."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def _loads(payload: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    try:
        return json.loads(payload or "{}")
    except json.JSONDecodeError:
        return {"raw": payload}


def write_briefing(watch_json: str) -> dict:
    """Format a short operational briefing from a Watch payload.

    Args:
        watch_json: JSON string returned by watch_conditions.

    Returns:
        script (on-air), social_blurb, and the facts used. Does not invent
        observations or hazards that are not in the payload.
    """
    watch = _loads(watch_json)
    loc = watch.get("location") or {}
    city = loc.get("city") or "the target"
    office = loc.get("cwa") or "NWS"
    obs = watch.get("observation") or {}
    hazards = watch.get("hazards") or []
    periods = watch.get("forecast_periods") or []

    temp = obs.get("temperature_f")
    sky = obs.get("text") or "conditions unavailable"
    station = obs.get("station_id") or "station n/a"
    temp_bit = f"{temp}°F" if temp is not None else "temperature unavailable"

    if hazards:
        headlines = [h.get("event") or h.get("headline") or "hazard" for h in hazards[:3]]
        hazard_line = "Active: " + "; ".join(headlines) + "."
    else:
        hazard_line = "No active NWS watches or warnings at this point."

    near_term = ""
    if periods:
        p0 = periods[0]
        near_term = (
            f"{p0.get('name')}: {p0.get('forecast')} "
            f"({p0.get('temperature')}{p0.get('unit') or 'F'})."
        ).strip()

    script = (
        f"WFAD briefing for {city}. "
        f"Now at {station}: {sky}, {temp_bit}. "
        f"{hazard_line} "
        f"{near_term} "
        f"Source: NWS {office} via api.weather.gov. Do not add unsourced detail."
    ).strip()

    social = f"{city}: {sky}, {temp_bit}. {hazard_line}"
    if len(social) > 260:
        social = social[:257] + "..."

    return {
        "status": "success",
        "location": city,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "script": script,
        "social_blurb": social,
        "hazard_count": len(hazards),
        "facts": {
            "temperature_f": temp,
            "sky": sky,
            "station_id": station,
            "cwa": office,
            "near_term": near_term,
            "failures": watch.get("failures") or [],
        },
        "sources": ["api.weather.gov"],
    }
