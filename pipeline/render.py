"""Compose scenes into a vertical 9:16 MP4 (Ken Burns motion + burned captions).

This module is pure composition: it has no network or TTS dependencies, so it
can be driven by the full pipeline or by the offline demo alike.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import Config
from .tts import CaptionCue


@dataclass
class RenderScene:
    image_path: str
    duration: float
    cues: list[CaptionCue] = field(default_factory=list)
    audio_path: str = ""


def _ken_burns(clip, duration: float, cfg: Config, zoom_out: bool):
    """Return a slowly zooming clip; scale stays >= 1 to avoid borders."""
    z = cfg.ken_burns_zoom
    if zoom_out:
        factor = lambda t: 1.0 + z * (1.0 - min(t, duration) / duration)
    else:
        factor = lambda t: 1.0 + z * (min(t, duration) / duration)
    return clip.resized(factor).with_position("center")


def _caption_clip(cue: CaptionCue, cfg: Config):
    from moviepy import TextClip
    y = int(cfg.height * cfg.caption_y_ratio)
    txt = TextClip(
        text=cue.text,
        font=cfg.font,
        font_size=cfg.font_size,
        color=cfg.caption_color,
        stroke_color=cfg.caption_stroke,
        stroke_width=cfg.caption_stroke_width,
        method="caption",
        size=(int(cfg.width * 0.86), None),
        text_align="center",
    )
    return (txt.with_start(cue.start)
               .with_duration(max(0.1, cue.end - cue.start))
               .with_position(("center", y)))


def _scene_clip(scene: RenderScene, idx: int, cfg: Config):
    from moviepy import ImageClip, AudioFileClip, CompositeVideoClip

    base = ImageClip(scene.image_path).with_duration(scene.duration)
    base = _ken_burns(base, scene.duration, cfg, zoom_out=(idx % 2 == 1))

    layers = [base] + [_caption_clip(c, cfg) for c in scene.cues]
    clip = CompositeVideoClip(layers, size=cfg.size).with_duration(scene.duration)

    if scene.audio_path:
        clip = clip.with_audio(AudioFileClip(scene.audio_path))
    return clip


def render_video(scenes: list[RenderScene], out_path: str, cfg: Config) -> str:
    from moviepy import concatenate_videoclips

    clips = [_scene_clip(s, i, cfg) for i, s in enumerate(scenes)]
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        out_path,
        fps=cfg.fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger=None,
    )
    for c in clips:
        c.close()
    final.close()
    return out_path
