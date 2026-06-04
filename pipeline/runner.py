"""End-to-end orchestration: a topic or a JSON script becomes a finished MP4."""
from __future__ import annotations

from pathlib import Path

from .config import Config
from .models import Script
from .render import RenderScene, render_video
from .script_gen import generate_script
from .tts import synthesize
from . import images


def build_from_script(script: Script, cfg: Config) -> str:
    work = Path(cfg.work_dir) / script.slug
    work.mkdir(parents=True, exist_ok=True)
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    render_scenes: list[RenderScene] = []
    for i, scene in enumerate(script.scenes):
        print(f"[scene {i + 1}/{len(script.scenes)}] {scene.caption[:30]}…")

        # 1) narration + word-synced caption cues
        audio_path = str(work / f"scene_{i:02d}.mp3")
        duration, cues = synthesize(
            scene.narration, audio_path, cfg, fallback_caption=scene.caption
        )

        # 2) visual (explicit path overrides search)
        img_path = scene.image or str(work / f"scene_{i:02d}.jpg")
        if not scene.image:
            images.get_image(scene.image_query, cfg, img_path, caption=scene.caption)

        render_scenes.append(
            RenderScene(image_path=img_path, duration=duration,
                        cues=cues, audio_path=audio_path)
        )

    out_path = str(out_dir / f"{script.slug}.mp4")
    print(f"[render] -> {out_path}")
    return render_video(render_scenes, out_path, cfg)


def build_from_topic(topic: str, n_scenes: int, cfg: Config) -> str:
    print(f"[script] generating for: {topic}")
    script = generate_script(topic, n_scenes, cfg)
    # persist the generated script next to the output for reuse/editing
    Path(cfg.output_dir).mkdir(parents=True, exist_ok=True)
    script.save(Path(cfg.output_dir) / f"{script.slug}.json")
    return build_from_script(script, cfg)
