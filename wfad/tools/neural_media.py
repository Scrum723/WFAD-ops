"""WFAD's media neural net: Gemini 3.5 Flash designs unique graphics/clips
from Doc weather products, then the media provider renders them.

Doc's neural network = weather modules. WFAD's = Gemini media designer.
"""

from __future__ import annotations

import json
import os
from typing import Any

from wfad.tools.render import render_hit_clip, render_hit_graphic

MODEL = os.environ.get("WFAD_AGENT_MODEL", "gemini-3.5-flash")


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


def _design_with_gemini(watch: dict[str, Any], briefing: dict[str, Any], focus: str) -> dict[str, Any]:
    loc = (watch.get("location") or {})
    city = loc.get("city") or "Rochester"
    obs = watch.get("observation") or {}
    media = watch.get("doc_media") or {}
    script = briefing.get("script") or ""
    prompt = (
        "You are WFAD media net. Design unique Doc Weather visuals. JSON only:\n"
        '{"graphic_prompt":"16:9 still","clip_prompt":"9:16 8s clip","document":"short written package"}\n'
        "Use ONLY these facts. Do not invent storms.\n"
        f"city={city} temp_f={obs.get('temperature_f')} sky={obs.get('text')} "
        f"station={obs.get('station_id')} radar={media.get('radar_latest')} "
        f"sat={media.get('satellite_geocolor')} script={script} focus={focus}\n"
        "Style: branded meteorologist desk, unique IP, no stock tornado cliches unless Watch has a tornado product."
    )
    client = _client()
    if client is None:
        return {
            "graphic_prompt": (
                f"16:9 Doc Weather graphic, {city}, {obs.get('text')}, "
                f"{obs.get('temperature_f')}F, station {obs.get('station_id')}, "
                f"radar still {media.get('radar_latest')}, no invented hazards."
            ),
            "clip_prompt": (
                f"9:16 8s Doc Weather hit, {city}. {script} "
                f"Animate desk + real radar URL {media.get('radar_latest')}."
            ),
            "document": script,
            "model": "heuristic",
        }
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        raw = (getattr(response, "text", None) or "").strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed["model"] = MODEL
            return parsed
    except Exception as exc:  # noqa: BLE001
        return {
            "graphic_prompt": f"{city} {obs.get('text')} {obs.get('temperature_f')}F Doc Weather board",
            "clip_prompt": script,
            "document": script,
            "model": "heuristic",
            "error_message": str(exc),
        }
    return {
        "graphic_prompt": script,
        "clip_prompt": script,
        "document": script,
        "model": "heuristic",
    }


def design_and_render_media(
    watch_json: str,
    briefing_json: str,
    focus: str = "hit",
) -> dict:
    """Gemini designs media from Doc products, then render graphic + clip.

    Args:
        watch_json: Watch payload (preferably Doc snapshot).
        briefing_json: write_briefing output.
        focus: hit, outlook_5day, severe, etc.

    Returns:
        Prompts plus render_hit_graphic / render_hit_clip results.
    """
    watch = json.loads(watch_json) if isinstance(watch_json, str) else watch_json
    briefing = json.loads(briefing_json) if isinstance(briefing_json, str) else briefing_json
    if not isinstance(watch, dict):
        watch = {}
    if not isinstance(briefing, dict):
        briefing = {}
    design = _design_with_gemini(watch, briefing, focus)
    graphic = render_hit_graphic(design.get("graphic_prompt") or "", aspect_ratio="16:9")
    clip = render_hit_clip(design.get("clip_prompt") or "", duration_s=8, aspect_ratio="9:16")
    return {
        "status": "success",
        "network": "wfad_gemini_media",
        "weather_source": watch.get("source"),
        "design": design,
        "graphic": graphic,
        "clip": clip,
        "media_provider": os.environ.get("MEDIA_PROVIDER", "stub"),
    }
