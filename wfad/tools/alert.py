"""Deterministic severity + routing. The model may add a one-line rationale
but must not override the rule table."""

from __future__ import annotations

import json
import os
from typing import Any

CRITICAL_NEEDLES = (
    "warning",
    "emergency",
    "tornado",
    "flash flood",
    "blizzard",
    "hurricane",
    "extreme",
)
HIGH_NEEDLES = ("watch",)
MODERATE_NEEDLES = ("advisory", "statement", "outlook")

RANK = {"ROUTINE": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def _loads(payload: str | dict[str, Any] | list[Any]) -> Any:
    if isinstance(payload, (dict, list)):
        return payload
    try:
        return json.loads(payload or "{}")
    except json.JSONDecodeError:
        return payload


def _blob(*parts: Any) -> str:
    return " ".join(json.dumps(p, default=str).lower() for p in parts)


def _recipients() -> list[str]:
    raw = os.environ.get("WFAD_RECIPIENTS", "operator@localhost")
    return [item.strip() for item in raw.split(",") if item.strip()]


def decide_alert(briefing_json: str, hazards_json: str = "[]") -> dict:
    """Assign severity, channels, and recipients from briefing + hazards.

    Args:
        briefing_json: JSON string from write_briefing (or equivalent facts).
        hazards_json: JSON list/string of NWS hazard objects from Watch.

    Returns:
        severity (ROUTINE|MODERATE|HIGH|CRITICAL), channels, recipients, rationale.
    """
    briefing = _loads(briefing_json)
    hazards = _loads(hazards_json)
    if isinstance(briefing, dict) and not hazards:
        # Allow a combined package.
        hazards = briefing.get("hazards") or (briefing.get("facts") or {}).get("hazards") or []
    if not isinstance(hazards, list):
        hazards = []

    text = _blob(briefing, hazards)
    severity = "ROUTINE"
    matched = "no active products"

    def bump(level: str, why: str) -> None:
        nonlocal severity, matched
        if RANK[level] > RANK[severity]:
            severity = level
            matched = why

    for hazard in hazards:
        event = " ".join(
            str(hazard.get(k) or "")
            for k in ("event", "headline", "severity", "urgency")
        ).lower()
        if any(n in event for n in CRITICAL_NEEDLES):
            bump("CRITICAL", event[:120] or "warning-class product")
        elif any(n in event for n in HIGH_NEEDLES):
            bump("HIGH", event[:120] or "watch-class product")
        elif any(n in event for n in MODERATE_NEEDLES):
            bump("MODERATE", event[:120] or "advisory-class product")

    if severity == "ROUTINE" and any(n in text for n in CRITICAL_NEEDLES):
        bump("CRITICAL", "warning language in briefing text")
    elif severity == "ROUTINE" and "watch" in text:
        bump("HIGH", "watch language in briefing text")

    if severity == "CRITICAL":
        channels = ["email", "social_stub"]
    elif severity == "HIGH":
        channels = ["email", "social_stub"]
    elif severity == "MODERATE":
        channels = ["email"]
    else:
        channels = ["email"]

    return {
        "status": "success",
        "severity": severity,
        "channels": channels,
        "recipients": _recipients(),
        "rationale": f"Rule table matched {severity} because: {matched}.",
        "rule": "deterministic; model may explain but must not override",
        "hazard_count": len(hazards),
    }
