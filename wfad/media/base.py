"""Provider contract. Story desk talks only to this, not to Veo or Imagine by name."""

from __future__ import annotations

from typing import Any, Protocol


class MediaProvider(Protocol):
    name: str

    def generate_graphic(self, prompt: str, aspect_ratio: str = "16:9") -> dict[str, Any]:
        """Still for a 5-day board, thumbnail, or first frame."""

    def generate_clip(self, prompt: str, duration_s: int = 8, aspect_ratio: str = "9:16") -> dict[str, Any]:
        """Short video. Providers may cap duration (Veo often 4–8s)."""

    def synthesize_speech(self, text: str) -> dict[str, Any]:
        """Read the approved script. Optional."""
