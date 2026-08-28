"""Swap media backends per contest without rewriting Story desk.

MEDIA_PROVIDER=stub|google
Future: grok (xAI Imagine) as a third provider with the same methods.
"""

from __future__ import annotations

import os

from .base import MediaProvider


def get_media_provider() -> MediaProvider:
    name = (os.environ.get("MEDIA_PROVIDER") or "stub").strip().lower()
    if name in {"google", "gemini", "vertex", "veo"}:
        from .google_media import GoogleMediaProvider

        return GoogleMediaProvider()
    from .stub import StubMediaProvider

    return StubMediaProvider()
