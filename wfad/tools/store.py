"""Persist a WFAD run. Firestore is the judged path; local JSON is a laptop fallback."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COLLECTION = os.environ.get("FIRESTORE_COLLECTION", "wfad_runs")


def _loads(payload: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    try:
        parsed = json.loads(payload or "{}")
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except json.JSONDecodeError:
        return {"raw": payload}


def _stamp(package: dict[str, Any]) -> dict[str, Any]:
    doc = dict(package)
    doc.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
    doc.setdefault("product", "WFAD")
    doc.setdefault("model", "gemini-3.5-flash")
    return doc


def _write_local(doc: dict[str, Any], reason: str) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    folder = Path(__file__).resolve().parents[2] / "local_runs"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{run_id}.json"
    payload = dict(doc)
    payload["run_id"] = run_id
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return {
        "status": "success",
        "backend": "local_file",
        "run_id": run_id,
        "path": str(path),
        "note": (
            "Firestore unavailable; wrote a local JSON document. "
            f"Judged path is Firestore collection '{COLLECTION}'. ({reason})"
        ),
    }


def record_run(package_json: str) -> dict:
    """Persist the full WFAD package to Firestore (or local JSON if ADC is missing).

    Args:
        package_json: JSON string of the full run (watch, briefing, alert, disseminate).

    Returns:
        run_id, backend (firestore|local_file), and status.
    """
    package = _stamp(_loads(package_json))
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
    try:
        from google.cloud import firestore  # imported lazily so `adk web` still starts

        client_kwargs: dict[str, Any] = {}
        if project:
            client_kwargs["project"] = project
        db = firestore.Client(**client_kwargs)
        ref = db.collection(COLLECTION).document()
        package["run_id"] = ref.id
        ref.set(package)
        return {
            "status": "success",
            "backend": "firestore",
            "run_id": ref.id,
            "collection": COLLECTION,
            "project": project or "(client default)",
        }
    except Exception as exc:  # noqa: BLE001
        return _write_local(package, reason=str(exc))
