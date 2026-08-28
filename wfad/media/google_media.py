"""Google AI Studio / Vertex path. Same google-genai client WFAD already depends on.

Does not use Google One credits (those stay in the Gemini app / Flow).
Uses GOOGLE_API_KEY and/or Vertex ADC on wfad-506515.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any


def _out_dir() -> Path:
    raw = os.environ.get("WFAD_MEDIA_DIR") or str(
        Path.home() / "Desktop" / "Doc Weather Content" / "assets"
    )
    path = Path(raw).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


class GoogleMediaProvider:
    name = "google"

    def __init__(self) -> None:
        self.image_model = os.environ.get("GOOGLE_IMAGE_MODEL", "gemini-3.1-flash-image")
        self.video_model = os.environ.get(
            "GOOGLE_VIDEO_MODEL", "veo-3.1-fast-generate-preview"
        )
        self.tts_model = os.environ.get("GOOGLE_TTS_MODEL", "gemini-2.5-flash-preview-tts")

    def _client(self):
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
        if not api_key:
            raise RuntimeError(
                "Google media needs GOOGLE_API_KEY (AI Studio) or "
                "GOOGLE_GENAI_USE_VERTEXAI=TRUE with ADC."
            )
        return genai.Client(api_key=api_key)

    def generate_graphic(self, prompt: str, aspect_ratio: str = "16:9") -> dict[str, Any]:
        try:
            client = self._client()
            response = client.models.generate_content(
                model=self.image_model,
                contents=prompt,
            )
            path = _out_dir() / f"graphic-{uuid.uuid4().hex[:8]}.png"
            saved = None
            for cand in getattr(response, "candidates", None) or []:
                content = getattr(cand, "content", None)
                for part in getattr(content, "parts", None) or []:
                    inline = getattr(part, "inline_data", None)
                    if inline and getattr(inline, "data", None):
                        path.write_bytes(inline.data)
                        saved = str(path)
                        break
            if not saved:
                return {
                    "status": "error",
                    "provider": self.name,
                    "error_message": "No image bytes in response. Check model access / billing.",
                    "model": self.image_model,
                }
            return {
                "status": "success",
                "provider": self.name,
                "model": self.image_model,
                "path": saved,
                "aspect_ratio": aspect_ratio,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "provider": self.name,
                "model": self.image_model,
                "error_message": str(exc),
            }

    def generate_clip(self, prompt: str, duration_s: int = 8, aspect_ratio: str = "9:16") -> dict[str, Any]:
        try:
            client = self._client()
            from google.genai import types

            seconds = 8 if duration_s > 8 else max(4, duration_s)
            operation = client.models.generate_videos(
                model=self.video_model,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    duration_seconds=seconds,
                ),
            )
            return {
                "status": "pending",
                "provider": self.name,
                "model": self.video_model,
                "operation": str(getattr(operation, "name", operation)),
                "note": (
                    "Veo job started. Poll or download from AI Studio/Vertex. "
                    "Omni scene-extend is the path for clips longer than ~8s."
                ),
                "duration_s": seconds,
                "aspect_ratio": aspect_ratio,
                "path": None,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "provider": self.name,
                "model": self.video_model,
                "error_message": str(exc),
                "note": "Google One app credits will not pay this API call.",
            }

    def synthesize_speech(self, text: str) -> dict[str, Any]:
        return {
            "status": "not_wired",
            "provider": self.name,
            "model": self.tts_model,
            "note": "Next slice: Gemini TTS of the approved script.",
            "text": (text or "")[:500],
        }
