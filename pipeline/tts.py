"""Narration via Edge TTS (free, no API key) with word-level timing.

`synthesize` returns the audio file duration and a list of CaptionCue objects
whose timings are derived from Edge TTS WordBoundary events, so on-screen
captions stay in sync with the voice.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .config import Config


@dataclass
class CaptionCue:
    start: float   # seconds
    end: float     # seconds
    text: str


async def _synth(text: str, out_path: str, cfg: Config) -> list[dict]:
    import edge_tts  # lazy import so the rest of the pipeline imports without it

    communicate = edge_tts.Communicate(
        text, voice=cfg.voice, rate=cfg.rate, volume=cfg.volume
    )
    boundaries: list[dict] = []
    with open(out_path, "wb") as fh:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                boundaries.append(chunk)
    return boundaries


def _group_cues(boundaries: list[dict], max_chars: int) -> list[CaptionCue]:
    """Merge word boundaries into readable caption lines.

    Edge TTS reports offset/duration in 100-nanosecond units. We accumulate
    words until a sentence break or the character budget is hit.
    """
    cues: list[CaptionCue] = []
    buf = ""
    start = None
    last_end = 0.0
    breakers = "。、！？!?,. "

    for b in boundaries:
        word = b.get("text", "")
        s = b["offset"] / 1e7
        e = (b["offset"] + b["duration"]) / 1e7
        last_end = e
        if start is None:
            start = s
        buf += word
        flush = len(buf) >= max_chars or any(c in breakers for c in word)
        if flush and buf.strip():
            cues.append(CaptionCue(start, e, buf.strip(" 、。")))
            buf, start = "", None
    if buf.strip():
        cues.append(CaptionCue(start or 0.0, last_end, buf.strip(" 、。")))
    return cues


def _audio_duration(path: str) -> float:
    from moviepy import AudioFileClip
    clip = AudioFileClip(path)
    d = clip.duration
    clip.close()
    return d


def synthesize(text: str, out_path: str, cfg: Config,
               fallback_caption: str = "") -> tuple[float, list[CaptionCue]]:
    """Render `text` to `out_path` (mp3). Returns (duration_sec, cues)."""
    boundaries = asyncio.run(_synth(text, out_path, cfg))
    duration = _audio_duration(out_path)
    cues = _group_cues(boundaries, cfg.caption_max_chars)
    if not cues:  # some voices emit no boundaries; show whole caption
        cues = [CaptionCue(0.0, duration, fallback_caption or text)]
    return duration, cues
