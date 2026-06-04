#!/usr/bin/env python3
"""CLI entrypoint for the history-pov short-video pipeline.

Examples:
    # From a ready-made JSON script (no API key needed; uses free TTS + Wikimedia)
    python make_video.py --script scripts/sample_sengoku.json

    # From a one-line topic (requires an LLM provider + key set in config/.env)
    python make_video.py --topic "本能寺の変" --scenes 6
"""
from __future__ import annotations

import argparse
import sys

from pipeline.config import load_config
from pipeline.models import Script
from pipeline.runner import build_from_script, build_from_topic


def main() -> int:
    ap = argparse.ArgumentParser(description="AI vertical short-video generator")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--script", help="path to a JSON script")
    src.add_argument("--topic", help="one-line topic (needs an LLM provider)")
    ap.add_argument("--scenes", type=int, default=6, help="scene count for --topic")
    ap.add_argument("--config", default="config.yaml", help="path to config.yaml")
    ap.add_argument("--voice", help="override TTS voice (e.g. ja-JP-KeitaNeural)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.voice:
        cfg.voice = args.voice

    if args.script:
        out = build_from_script(Script.load(args.script), cfg)
    else:
        out = build_from_topic(args.topic, args.scenes, cfg)

    print(f"\n✅ Done: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
