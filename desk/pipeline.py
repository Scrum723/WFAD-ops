"""Deterministic Autopilot: Gemini understood the ask; tools do the weather."""

from __future__ import annotations

import json
from typing import Any

from wfad.tools.alert import decide_alert
from wfad.tools.forecast import write_briefing
from wfad.tools.neural_media import design_and_render_media
from wfad.tools.story import approve_package, draft_story, revise_story
from wfad.tools.watch import watch_conditions


def run_draft(location: str, focus: str = "hit") -> dict[str, Any]:
    watch = watch_conditions(city=location)
    briefing = write_briefing(json.dumps(watch))
    alert = decide_alert(json.dumps(briefing), json.dumps(watch.get("hazards") or []))
    story = draft_story(
        json.dumps({"watch": watch, "briefing": briefing, "alert": alert}),
        focus=focus or "hit",
    )
    neural = design_and_render_media(
        json.dumps(watch), json.dumps(briefing), focus=focus or "hit"
    )
    return {
        "watch": watch,
        "briefing": briefing,
        "alert": alert,
        "story": story,
        "neural": neural,
        "graphic": neural.get("graphic") or {},
        "clip": neural.get("clip") or {},
    }


def run_revise(story: dict[str, Any], notes: str) -> dict[str, Any]:
    updated = revise_story(json.dumps(story), notes=notes)
    return {"story": updated}


def run_approve(story: dict[str, Any]) -> dict[str, Any]:
    return {"story": approve_package(json.dumps(story))}


def package_card(bundle: dict[str, Any]) -> dict[str, Any]:
    story = bundle.get("story") or {}
    hit = (story.get("products") or {}).get("hit") or {}
    alert = bundle.get("alert") or {}
    watch = bundle.get("watch") or {}
    loc = watch.get("location") or {}
    graphic = bundle.get("graphic") or {}
    clip = bundle.get("clip") or {}
    leesa = story.get("leesa") or {}
    return {
        "story_id": story.get("story_id"),
        "approval": story.get("approval") or "draft",
        "location": story.get("location") or loc.get("city"),
        "severity": story.get("severity") or alert.get("severity"),
        "script": hit.get("script"),
        "social_blurb": hit.get("social_blurb"),
        "clip_prompt": hit.get("clip_prompt"),
        "station_id": (watch.get("observation") or {}).get("station_id"),
        "graphic_status": graphic.get("status") or graphic.get("provider"),
        "clip_status": clip.get("status") or clip.get("provider"),
        "media_provider": graphic.get("provider") or clip.get("provider") or "stub",
        "weather_source": watch.get("source"),
        "neural_model": (bundle.get("neural") or {}).get("design", {}).get("model"),
        "bundle_dir": leesa.get("bundle_dir"),
        "handed_off": bool(leesa.get("handed_off")),
    }
