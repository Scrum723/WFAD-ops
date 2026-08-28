"""Story desk — addition to WFAD, not a new agent and not Leesa.

draft → revise → approve are three tools on the same root_agent.
Nothing goes to Leesa until approve_package. Ground only in Watch/Forecast/Alert.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CTA = "https://linktr.ee/URP"


def _loads(payload: str | dict[str, Any] | list[Any]) -> Any:
    if isinstance(payload, (dict, list)):
        return payload
    try:
        return json.loads(payload or "{}")
    except json.JSONDecodeError:
        return {"raw": payload}


def _slug(location: str, when: datetime) -> str:
    place = re.sub(r"[^a-z0-9]+", "-", (location or "rochester").lower()).strip("-")
    return f"{when.strftime('%Y-%m-%d')}-{place}-hit"


def _bundles_root() -> Path:
    raw = os.environ.get("WFAD_LEESA_BUNDLES") or str(
        Path.home() / "Desktop" / "Doc Weather Content" / "bundles"
    )
    path = Path(raw).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _empty_product(kind: str, note: str) -> dict[str, Any]:
    return {"kind": kind, "status": "not_drafted", "note": note}


def draft_story(package_json: str, focus: str = "hit") -> dict:
    """Draft a Story desk package from Watch + Forecast + Alert. Do not post.

    Args:
        package_json: JSON of watch, briefing, and alert (or a prior story).
        focus: Which product to flesh out first. Use "hit" for the 30-60s clip.

    Returns:
        A story object with approval=draft. Other forecast products are stubs
        until later slices. Facts must come from the package, not invention.
    """
    package = _loads(package_json)
    if not isinstance(package, dict):
        package = {"raw": package}

    watch = package.get("watch") or {}
    briefing = package.get("briefing") or package
    alert = package.get("alert") or {}
    loc = (watch.get("location") or {})
    city = loc.get("city") or briefing.get("location") or "Rochester"
    now = datetime.now(timezone.utc)
    story_id = "story-" + uuid.uuid4().hex[:10]
    script = briefing.get("script") or ""
    social = briefing.get("social_blurb") or script[:260]
    facts = briefing.get("facts") or {}
    hazards = watch.get("hazards") or []
    severity = alert.get("severity") or package.get("severity") or "ROUTINE"

    clip_prompt = (
        f"30-60s vertical Doc Weather hit for {city}. "
        f"On-air script (do not add unsourced weather): {script} "
        f"Style: unique branded meteorologist desk, radar stills only if they "
        f"match NWS facts, no stock storm stock-footage cliches. CTA {CTA}."
    )

    hit = {
        "kind": "hit",
        "status": "draft",
        "duration_s": 45,
        "script": script,
        "social_blurb": social,
        "clip_prompt": clip_prompt,
        "video_file": None,
        "note": "Clip is a prompt + script this slice. Unique video gen comes next.",
    }

    story = {
        "status": "success",
        "story_id": story_id,
        "approval": "draft",
        "focus": focus or "hit",
        "location": city,
        "severity": severity,
        "issued_at": now.isoformat(),
        "grounded_in": {
            "station_id": (watch.get("observation") or {}).get("station_id")
            or facts.get("station_id"),
            "cwa": loc.get("cwa") or facts.get("cwa"),
            "hazard_count": len(hazards),
            "temperature_f": facts.get("temperature_f"),
        },
        "products": {
            "hit": hit,
            "debrief_3to5min": _empty_product(
                "debrief_3to5min", "Next slice after hit + approve works."
            ),
            "outlook_3day": _empty_product("outlook_3day", "Not this slice."),
            "outlook_5day": _empty_product("outlook_5day", "Not this slice."),
            "outlook_10day": _empty_product("outlook_10day", "Not this slice."),
            "severe": _empty_product("severe", "Only when Alert is HIGH/CRITICAL."),
            "hurricane": _empty_product("hurricane", "Only when Watch has tropical."),
            "winter": _empty_product("winter", "Only when Watch has winter products."),
            "longform": _empty_product("longform", "In-depth after the short products."),
        },
        "revisions": [],
        "leesa": {"handed_off": False},
        "cta": CTA,
    }
    return story


def revise_story(story_json: str, notes: str) -> dict:
    """Apply human (or voice-to-text) notes to a draft. Does not approve or post.

    Args:
        story_json: JSON from draft_story or a prior revise_story.
        notes: Plain text edits. Voice-to-text lands here later.

    Returns:
        Updated story, still approval=draft unless notes explicitly say approve
        (they must still call approve_package).
    """
    story = _loads(story_json)
    if not isinstance(story, dict):
        return {"status": "error", "error_message": "story_json was not a story object"}
    if story.get("approval") == "approved":
        return {
            "status": "error",
            "error_message": "Already approved. Draft a new story to change facts.",
            "story_id": story.get("story_id"),
        }

    notes = (notes or "").strip()
    hit = (story.get("products") or {}).get("hit") or {}
    script = hit.get("script") or ""
    if notes:
        # Keep the original script; append a desk note so the model + human see it.
        # The agent rewrites the spoken script in its reply; this tool stores intent.
        hit["desk_notes"] = notes
        hit["status"] = "revised"
        if "cta" not in notes.lower():
            pass
        story.setdefault("revisions", []).append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "notes": notes,
            }
        )
        # If the human pasted a replacement script after "SCRIPT:", use it.
        marker = "SCRIPT:"
        if marker.lower() in notes.lower():
            idx = notes.lower().index(marker.lower())
            replacement = notes[idx + len(marker) :].strip()
            if replacement:
                hit["script"] = replacement
                hit["social_blurb"] = replacement[:260]
        elif len(notes) > 40 and not script.startswith(notes[:40]):
            hit["revision_instruction"] = notes

    products = story.setdefault("products", {})
    products["hit"] = hit
    story["approval"] = "draft"
    story["status"] = "success"
    return story


def approve_package(story_json: str) -> dict:
    """Human sign-off. Write a Leesa bundle. Do not post to social.

    Args:
        story_json: JSON story after draft_story / revise_story.

    Returns:
        approval=approved, bundle path under Doc Weather Content/bundles.
        Leesa (not WFAD) captions and posts from that folder.
    """
    story = _loads(story_json)
    if not isinstance(story, dict):
        return {"status": "error", "error_message": "story_json was not a story object"}

    city = story.get("location") or "Rochester"
    now = datetime.now(timezone.utc)
    slug = _slug(city, now)
    bundle = _bundles_root() / slug
    bundle.mkdir(parents=True, exist_ok=True)

    hit = (story.get("products") or {}).get("hit") or {}
    script = hit.get("script") or ""
    social = hit.get("social_blurb") or script[:260]
    title = f"{city} WFAD hit — {now.strftime('%Y-%m-%d')}"

    insight = (
        f"# {title}\n\n"
        f"{social}\n\n"
        f"{script}\n\n"
        f"Severity: {story.get('severity') or 'ROUTINE'}\n"
        f"Grounded in NWS facts via WFAD Watch. Do not add unsourced detail.\n\n"
        f"Full links → {CTA}\n"
    )
    meta = (
        f'title_hint: "{title}"\n'
        f"platforms: [x, instagram, tiktok, youtube]\n"
        f"content_type: bundle\n"
        f"tags: [WNY, {city}, WFAD]\n"
        f'cta: "{CTA}"\n'
        f'notes: "Approved WFAD story {story.get("story_id")}. Video file added when clip gen lands."\n'
        f"approval: approved\n"
        f'severity: "{story.get("severity") or "ROUTINE"}"\n'
    )
    (bundle / "insight.md").write_text(insight, encoding="utf-8")
    (bundle / "meta.yaml").write_text(meta, encoding="utf-8")
    (bundle / "CLIP_PROMPT.txt").write_text(hit.get("clip_prompt") or "", encoding="utf-8")
    (bundle / "story.json").write_text(
        json.dumps({**story, "approval": "approved"}, indent=2, default=str),
        encoding="utf-8",
    )

    story["approval"] = "approved"
    story["approved_at"] = now.isoformat()
    story["leesa"] = {
        "handed_off": True,
        "bundle_dir": str(bundle),
        "insight": str(bundle / "insight.md"),
        "meta": str(bundle / "meta.yaml"),
        "posted": False,
        "note": "Leesa scans this folder. WFAD does not post to four platforms.",
    }
    story["status"] = "success"
    return story
