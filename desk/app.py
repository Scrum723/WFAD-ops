"""Grok-like WFAD desk. Gemini understands. Autopilot designs. You approve."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from desk.gemini import understand
from desk.pipeline import package_card, run_approve, run_draft, run_revise

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / "wfad" / ".env")
except Exception:  # noqa: BLE001
    pass

app = FastAPI(title="WFAD desk", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(WEB)), name="static")

_state: dict[str, Any] = {
    "autopilot": True,
    "pending": None,
    "history": [],
}


class TurnIn(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    autopilot: bool | None = None


class SettingsIn(BaseModel):
    autopilot: bool


def _reply(role: str, text: str, card: dict[str, Any] | None = None) -> dict[str, Any]:
    item = {"role": role, "text": text, "card": card}
    _state["history"].append(item)
    _state["history"] = _state["history"][-40:]
    return item


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB / "index.html")


@app.get("/api/state")
async def state() -> dict[str, Any]:
    pending = _state["pending"]
    return {
        "autopilot": _state["autopilot"],
        "model": os.environ.get("WFAD_AGENT_MODEL", "gemini-3.5-flash"),
        "media_provider": os.environ.get("MEDIA_PROVIDER", "stub"),
        "pending": package_card(pending) if pending else None,
        "history": _state["history"],
    }


@app.post("/api/settings")
async def settings(body: SettingsIn) -> dict[str, Any]:
    _state["autopilot"] = bool(body.autopilot)
    return {"autopilot": _state["autopilot"]}


@app.post("/api/turn")
async def turn(body: TurnIn) -> dict[str, Any]:
    if body.autopilot is not None:
        _state["autopilot"] = bool(body.autopilot)
    message = body.message.strip()
    _reply("user", message)
    pending = _state["pending"]
    intent = understand(message, autopilot=_state["autopilot"], has_pending=bool(pending))
    action = intent["action"]
    if action == "revise" and not pending:
        action = "draft"
    if action == "approve" and not pending:
        assistant = _reply(
            "assistant",
            "Nothing is waiting. Ask for a package first — Autopilot will design it.",
        )
        return {"ok": True, "intent": intent, "assistant": assistant, "pending": None}

    if action == "chat":
        assistant = _reply(
            "assistant",
            "I am WFAD. Name a place and a product (hit, 5-day, severe) and I will "
            "design the package. Autopilot runs Watch → Story and stops for your approval. "
            "Leesa posts only after you approve.",
        )
        return {"ok": True, "intent": intent, "assistant": assistant, "pending": None}

    if action == "revise" and pending:
        bundle = run_revise(pending["story"], intent.get("notes") or message)
        pending["story"] = bundle["story"]
        _state["pending"] = pending
        card = package_card(pending)
        assistant = _reply(
            "assistant",
            f"Revised draft {card.get('story_id')}. Still waiting on your approval — not sent to Leesa.",
            card,
        )
        return {"ok": True, "intent": intent, "assistant": assistant, "pending": card}

    if action == "approve" and pending:
        bundle = run_approve(pending["story"])
        _state["pending"] = None
        card = package_card({"story": bundle["story"], "watch": pending.get("watch")})
        path = card.get("bundle_dir") or "the Leesa bundles folder"
        assistant = _reply(
            "assistant",
            f"Approved. Bundle written for Leesa at {path}. WFAD did not post.",
            card,
        )
        return {"ok": True, "intent": intent, "assistant": assistant, "pending": None}

    bundle = run_draft(intent["location"], focus=intent.get("focus") or "hit")
    _state["pending"] = bundle
    card = package_card(bundle)
    mode = "Autopilot" if _state["autopilot"] else "Desk"
    assistant = _reply(
        "assistant",
        f"{mode} designed a {intent.get('focus') or 'hit'} for {card.get('location')} "
        f"({card.get('severity')}). Understood via {intent.get('model')}: {intent.get('summary')}. "
        f"Media backend: {card.get('media_provider')}. Approve to hand off to Leesa.",
        card,
    )
    return {"ok": True, "intent": intent, "assistant": assistant, "pending": card}


@app.post("/api/approve")
async def approve() -> dict[str, Any]:
    pending = _state["pending"]
    if not pending:
        return {"ok": False, "error": "no pending package"}
    bundle = run_approve(pending["story"])
    _state["pending"] = None
    card = package_card({"story": bundle["story"], "watch": pending.get("watch")})
    assistant = _reply(
        "assistant",
        f"Approved. Leesa bundle: {card.get('bundle_dir')}",
        card,
    )
    return {"ok": True, "assistant": assistant, "pending": None}


def run() -> None:
    import uvicorn

    uvicorn.run(
        "desk.app:app",
        host="127.0.0.1",
        port=int(os.environ.get("WFAD_DESK_PORT", "8788")),
        reload=False,
    )


if __name__ == "__main__":
    run()
