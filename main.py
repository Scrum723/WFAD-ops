"""Cloud Run entry. ADK FastAPI app plus /trigger for Pub/Sub and the demo POST.

Official path: gcloud run deploy --source . from this folder.
"""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

from trigger.pubsub_handler import register_trigger_routes

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# In-memory sessions are enough for the contest. Set SESSION_SERVICE_URI to
# a SQLAlchemy URL if you want persistence (requires sqlalchemy).
SESSION_SERVICE_URI = os.environ.get("SESSION_SERVICE_URI")
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
SERVE_WEB_INTERFACE = True


def _build_app() -> FastAPI:
    kwargs: dict = dict(
        allow_origins=ALLOWED_ORIGINS,
        web=SERVE_WEB_INTERFACE,
    )
    if SESSION_SERVICE_URI:
        kwargs["session_service_uri"] = SESSION_SERVICE_URI
    try:
        app = get_fast_api_app(agents_dir=AGENT_DIR, **kwargs)
    except TypeError:
        app = get_fast_api_app(agent_dir=AGENT_DIR, **kwargs)
    register_trigger_routes(app)
    return app


app: FastAPI = _build_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
