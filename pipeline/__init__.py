"""history-pov: AI-generated vertical (9:16) short-video pipeline.

Modules:
    config      - load settings from config.yaml / .env
    script_gen  - produce a Script (LLM-backed or from JSON)
    tts         - narration audio + word timing via Edge TTS (free, no key)
    images      - source visuals from Wikimedia Commons, with a PIL fallback
    render      - compose scenes into a 9:16 MP4 (Ken Burns + burned captions)
    runner      - orchestrate the full topic -> video flow
"""

from .config import Config, load_config  # noqa: F401
