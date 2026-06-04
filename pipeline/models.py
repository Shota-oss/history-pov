"""Data model for a video script."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Scene:
    narration: str                       # text spoken by the TTS voice
    caption: str = ""                    # on-screen text (defaults to narration)
    image_query: str = ""                # Wikimedia Commons search term
    image: str = ""                      # explicit local image path (overrides query)

    def __post_init__(self) -> None:
        if not self.caption:
            self.caption = self.narration
        if not self.image_query:
            # fall back to the caption as a search hint
            self.image_query = self.caption


@dataclass
class Script:
    title: str
    topic: str = ""
    scenes: list[Scene] = field(default_factory=list)

    @property
    def slug(self) -> str:
        s = re.sub(r"[^\w぀-ヿ一-鿿-]+", "_", self.title).strip("_")
        return s[:60] or "video"

    @classmethod
    def from_dict(cls, data: dict) -> "Script":
        scenes = [Scene(**s) for s in data.get("scenes", [])]
        return cls(title=data.get("title", "untitled"),
                   topic=data.get("topic", ""),
                   scenes=scenes)

    @classmethod
    def load(cls, path: str | Path) -> "Script":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    def save(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, ensure_ascii=False, indent=2)
