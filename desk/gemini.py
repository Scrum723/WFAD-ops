"""Gemini 3.5 Flash: understand the user. Tools still own weather facts."""

from __future__ import annotations

import json
import os
import re
from typing import Any

MODEL = os.environ.get("WFAD_AGENT_MODEL", "gemini-3.5-flash")

KNOWN = {
    "rochester": "Rochester, NY",
    "buffalo": "Buffalo, NY",
    "syracuse": "Syracuse, NY",
    "jamestown": "Jamestown, NY",
    "erie": "Erie, PA",
}

FOCUS_WORDS = (
    ("10-day", "outlook_10day"),
    ("10 day", "outlook_10day"),
    ("5-day", "outlook_5day"),
    ("5 day", "outlook_5day"),
    ("3-day", "outlook_3day"),
    ("3 day", "outlook_3day"),
    ("hurricane", "hurricane"),
    ("winter", "winter"),
    ("severe", "severe"),
    ("debrief", "debrief_3to5min"),
    ("longform", "longform"),
    ("long-form", "longform"),
    ("clip", "hit"),
    ("hit", "hit"),
)


def _client():
    from google import genai

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    use_vertex = (os.environ.get("GOOGLE_GENAI_USE_VERTEXAI") or "").upper() in {
        "1",
        "TRUE",
        "YES",
    }
    if use_vertex:
        return genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", "wfad-506515"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
        )
    if api_key:
        return genai.Client(api_key=api_key)
    return None


def fallback_intent(message: str) -> dict[str, Any]:
    text = (message or "").strip()
    lower = text.lower()
    location = "Rochester, NY"
    for key, label in KNOWN.items():
        if key in lower:
            location = label
            break
    action = "draft"
    if re.search(r"\b(approve|ship it|send to leesa|looks good|lgtm)\b", lower):
        action = "approve"
    elif re.search(r"\b(revise|change|instead|lead with|make it|rewrite)\b", lower):
        action = "revise"
    elif re.search(r"^\s*(hi|hello|hey|thanks)\s*[.!]?\s*$", lower):
        action = "chat"
    focus = "hit"
    for needle, value in FOCUS_WORDS:
        if needle in lower:
            focus = value
            break
    return {
        "location": location,
        "action": action,
        "focus": focus,
        "notes": text if action == "revise" else "",
        "summary": f"{action} {focus} for {location}",
        "model": "fallback",
    }


def understand(message: str, autopilot: bool, has_pending: bool) -> dict[str, Any]:
    """Gemini NLU. Falls back to rules if the model is unavailable."""
    base = fallback_intent(message)
    client = _client()
    if client is None:
        if autopilot and base["action"] == "chat":
            base["action"] = "draft"
        return base
    prompt = (
        "Extract WFAD desk intent. JSON only, no markdown.\n"
        '{"location":"Rochester, NY","action":"draft|revise|approve|chat",'
        '"focus":"hit|debrief_3to5min|outlook_3day|outlook_5day|outlook_10day|'
        'severe|hurricane|winter|longform","notes":"","summary":"one line"}\n'
        f"Autopilot={'on' if autopilot else 'off'}. Pending draft={'yes' if has_pending else 'no'}.\n"
        "Default location Rochester, NY. action=approve only if they clearly sign off. "
        "action=revise if they are editing copy. action=draft for a new package. "
        "If Autopilot is on and they name a place or a product, use draft not chat.\n"
        f"User: {message}"
    )
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        raw = (getattr(response, "text", None) or "").strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return base
        out = {
            "location": parsed.get("location") or base["location"],
            "action": parsed.get("action") or base["action"],
            "focus": parsed.get("focus") or base["focus"],
            "notes": parsed.get("notes") or (message if parsed.get("action") == "revise" else ""),
            "summary": parsed.get("summary") or base["summary"],
            "model": MODEL,
        }
        if out["action"] not in {"draft", "revise", "approve", "chat"}:
            out["action"] = base["action"]
        if autopilot and out["action"] == "chat" and any(
            k in message.lower() for k in list(KNOWN) + ["forecast", "clip", "package", "weather"]
        ):
            out["action"] = "draft"
        return out
    except Exception:  # noqa: BLE001
        if autopilot and base["action"] == "chat":
            base["action"] = "draft"
        return base
