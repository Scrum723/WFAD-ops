"""Story-desk render tools. Call the media provider; do not import Veo/Imagine by name."""

from __future__ import annotations

from wfad.media import get_media_provider


def render_hit_graphic(prompt: str, aspect_ratio: str = "16:9") -> dict:
    """Generate a custom still (thumbnail, 5-day board, first frame) from a grounded prompt.

    Args:
        prompt: Must include only weather facts from Watch/Forecast. No invented hazards.
        aspect_ratio: For example 16:9 or 9:16.

    Returns:
        Provider name, status, and file path when the backend writes a file.
    """
    provider = get_media_provider()
    result = provider.generate_graphic(prompt, aspect_ratio=aspect_ratio)
    result["tool"] = "render_hit_graphic"
    return result


def render_hit_clip(prompt: str, duration_s: int = 8, aspect_ratio: str = "9:16") -> dict:
    """Generate a short unique clip. Google Veo/Omni when MEDIA_PROVIDER=google.

    Args:
        prompt: Approved hit script plus visual direction. Ground in NWS facts.
        duration_s: Requested seconds. Google Veo often caps at 4–8s per shot.
        aspect_ratio: 9:16 for Reels/Shorts.

    Returns:
        Provider result. Longer debriefs are multiple clips, then stitch.
    """
    provider = get_media_provider()
    result = provider.generate_clip(prompt, duration_s=duration_s, aspect_ratio=aspect_ratio)
    result["tool"] = "render_hit_clip"
    return result
