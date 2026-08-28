"""Default until a contest-specific key is set. Always safe to import."""

from __future__ import annotations

from typing import Any


class StubMediaProvider:
    name = "stub"

    def generate_graphic(self, prompt: str, aspect_ratio: str = "16:9") -> dict[str, Any]:
        return {
            "status": "stub",
            "provider": self.name,
            "path": None,
            "note": "Set MEDIA_PROVIDER=google and GOOGLE_API_KEY (or Vertex) to render.",
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        }

    def generate_clip(self, prompt: str, duration_s: int = 8, aspect_ratio: str = "9:16") -> dict[str, Any]:
        return {
            "status": "stub",
            "provider": self.name,
            "path": None,
            "note": "Set MEDIA_PROVIDER=google to call Veo or Gemini Omni.",
            "prompt": prompt,
            "duration_s": duration_s,
            "aspect_ratio": aspect_ratio,
        }

    def synthesize_speech(self, text: str) -> dict[str, Any]:
        return {
            "status": "stub",
            "provider": self.name,
            "path": None,
            "note": "Google TTS / Live API later. Grok is not the contest voice.",
            "text": (text or "")[:500],
        }
