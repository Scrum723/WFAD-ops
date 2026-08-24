"""Cloud Run HTTP entry for Pub/Sub push and the demo POST.

Demo body (enough to prove background execution):

    {"location": "Rochester, NY", "reason": "scheduled_briefing"}

Pub/Sub push envelope is also accepted: message.data is base64 JSON.
"""

from __future__ import annotations

import base64
import json
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def parse_trigger_body(body: dict[str, Any]) -> dict[str, str]:
    """Accept a plain demo POST or a Pub/Sub push envelope."""
    if "message" in body and isinstance(body.get("message"), dict):
        raw = body["message"].get("data") or ""
        decoded: dict[str, Any] = {}
        if raw:
            try:
                decoded = json.loads(base64.b64decode(raw).decode("utf-8") or "{}")
            except Exception:  # noqa: BLE001
                decoded = {}
        if not isinstance(decoded, dict):
            decoded = {}
        return {
            "location": str(decoded.get("location") or "Rochester, NY"),
            "reason": str(decoded.get("reason") or "pubsub_push"),
        }
    return {
        "location": str(body.get("location") or "Rochester, NY"),
        "reason": str(body.get("reason") or "scheduled_briefing"),
    }


def trigger_prompt(location: str, reason: str) -> str:
    return (
        f"A background trigger arrived.\n"
        f"Location: {location}\n"
        f"Reason: {reason}\n\n"
        "Run the full WFAD loop without asking for confirmation:\n"
        "1) watch_conditions for this location\n"
        "2) write_briefing from the watch payload\n"
        "3) decide_alert from the briefing and hazards\n"
        "4) disseminate_package for the decided channels\n"
        "5) record_run with the full package\n"
        "If a tool fails, record the failure and continue with remaining safe steps."
    )


async def run_wfad_loop(location: str, reason: str) -> dict[str, Any]:
    """Invoke root_agent once. Used by /trigger so Pub/Sub does not need a human."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from wfad.agent import root_agent

    app_name = "wfad"
    user_id = "wfad-trigger"
    session_id = f"trigger-{uuid.uuid4().hex[:12]}"
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)
    content = types.Content(
        role="user",
        parts=[types.Part(text=trigger_prompt(location, reason))],
    )
    final_text = ""
    tool_events: list[str] = []
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        author = getattr(event, "author", "") or ""
        if getattr(event, "content", None) and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "function_call", None):
                    tool_events.append(part.function_call.name)
                if getattr(part, "text", None):
                    final_text = part.text
        if hasattr(event, "is_final_response") and event.is_final_response():
            if event.content and event.content.parts:
                texts = [p.text for p in event.content.parts if getattr(p, "text", None)]
                if texts:
                    final_text = texts[-1]
    return {
        "status": "ok",
        "location": location,
        "reason": reason,
        "session_id": session_id,
        "tools_called": tool_events,
        "final_text": final_text,
    }


def register_trigger_routes(app: FastAPI) -> None:
    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "product": "WFAD"}

    @app.post("/trigger")
    @app.post("/pubsub")
    async def trigger(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        if not isinstance(body, dict):
            body = {}
        parsed = parse_trigger_body(body)
        try:
            result = await run_wfad_loop(parsed["location"], parsed["reason"])
            return JSONResponse(result)
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                {
                    "status": "error",
                    "location": parsed["location"],
                    "reason": parsed["reason"],
                    "error": str(exc),
                },
                status_code=500,
            )
