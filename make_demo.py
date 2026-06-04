#!/usr/bin/env python3
"""Offline demo — no network, no API keys, no TTS server required.

Builds a real 9:16 MP4 from a JSON script using generated gradient visuals and
synthesised ambient tones. Use it to verify the rendering pipeline anywhere
(e.g. a restricted CI/cloud box). For real narration + historical imagery,
use make_video.py instead.

    python make_demo.py --script scripts/sample_sengoku.json
"""
from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np

from pipeline.config import load_config
from pipeline.models import Script
from pipeline import images
from pipeline.render import RenderScene, render_video
from pipeline.tts import CaptionCue


def _tone_wav(path: str, duration: float, freq: float, fps: int = 44100) -> None:
    t = np.linspace(0, duration, int(duration * fps), endpoint=False)
    wave_data = 0.18 * np.sin(2 * np.pi * freq * t)
    # gentle fade in/out
    fade = int(0.15 * fps)
    env = np.ones_like(wave_data)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    samples = (wave_data * env * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fps)
        w.writeframes(samples.tobytes())


def main() -> int:
    ap = argparse.ArgumentParser(description="Offline render demo (no network)")
    ap.add_argument("--script", default="scripts/sample_sengoku.json")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="output/demo.mp4")
    args = ap.parse_args()

    cfg = load_config(args.config)
    cfg.image_provider = "none"           # force gradient fallback (no network)
    script = Script.load(args.script)

    work = Path(cfg.work_dir) / "demo"
    work.mkdir(parents=True, exist_ok=True)

    scenes: list[RenderScene] = []
    base_freq = 196.0                     # a calm low pad, stepping per scene
    for i, sc in enumerate(script.scenes):
        # ~0.13s per character, clamped to a pleasant short-video range
        duration = float(min(5.0, max(2.6, len(sc.caption) * 0.13)))

        img = str(work / f"demo_{i:02d}.jpg")
        images.get_image(sc.image_query, cfg, img, caption=sc.caption)

        audio = str(work / f"demo_{i:02d}.wav")
        _tone_wav(audio, duration, base_freq * (1 + 0.06 * i))

        scenes.append(RenderScene(
            image_path=img,
            duration=duration,
            cues=[CaptionCue(0.0, duration, sc.caption)],
            audio_path=audio,
        ))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out = render_video(scenes, args.out, cfg)
    print(f"\n✅ Demo written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
