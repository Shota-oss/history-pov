"""Configuration loading and defaults for the pipeline."""
from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - yaml is optional
    yaml = None

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:  # pragma: no cover
    pass

# A Japanese-capable font is required to render Japanese captions.
# On Debian/Ubuntu containers this path is provided by fonts-japanese-gothic.
_FONT_CANDIDATES = [
    "/etc/alternatives/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",  # macOS
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]


def _default_font() -> str:
    for p in _FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return _FONT_CANDIDATES[0]


@dataclass
class Config:
    # Output frame geometry (vertical short)
    width: int = 1080
    height: int = 1920
    fps: int = 30

    # Narration (Edge TTS voice names: run `edge-tts --list-voices`)
    voice: str = "ja-JP-NanamiNeural"
    rate: str = "+0%"
    volume: str = "+0%"

    # Captions
    font: str = field(default_factory=_default_font)
    font_size: int = 64
    caption_max_chars: int = 14          # group word boundaries into lines
    caption_color: str = "white"
    caption_stroke: str = "black"
    caption_stroke_width: int = 4
    caption_y_ratio: float = 0.74        # vertical position (0=top, 1=bottom)

    # Visuals
    ken_burns_zoom: float = 0.08         # fractional zoom over a scene
    image_provider: str = "wikimedia"    # "wikimedia" | "none" (PIL fallback)

    # Script generation
    llm_provider: str = "none"           # "anthropic" | "openai" | "none"
    llm_model: str = ""                  # provider default if empty

    # Paths
    output_dir: str = "output"
    work_dir: str = "output/_work"

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    def to_dict(self) -> dict:
        return asdict(self)


def load_config(path: str | os.PathLike | None = None) -> Config:
    """Load Config from a YAML file, falling back to defaults."""
    cfg = Config()
    if path and Path(path).exists() and yaml is not None:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        for key, value in data.items():
            if hasattr(cfg, key) and value is not None:
                setattr(cfg, key, value)
    return cfg
