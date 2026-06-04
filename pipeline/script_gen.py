"""Generate a Script from a topic using an LLM, or load one from JSON.

LLM access is optional. With ``llm_provider="none"`` (the default) you supply
your own JSON script (see scripts/sample_sengoku.json). With "anthropic" or
"openai" set, and the matching API key in the environment, a script is
generated automatically from a one-line topic.
"""
from __future__ import annotations

import json
import os

from .config import Config
from .models import Script

_SYSTEM = (
    "あなたは歴史系のショート動画（TikTok/Reels/YouTube Shorts、縦型9:16）の構成作家です。"
    "視聴者を冒頭3秒で引き込み、史実に忠実で、最後に余韻を残す台本を作ります。"
)

_PROMPT_TEMPLATE = """次のテーマで、縦型ショート動画の台本をJSONで作成してください。

テーマ: {topic}
シーン数: {n}

各シーンは1〜2文の短いナレーション。視覚的に絵になる被写体を image_query に英語で指定。
出力は次のJSONのみ（前後に説明文を付けない）:

{{
  "title": "キャッチーな日本語タイトル",
  "topic": "{topic}",
  "scenes": [
    {{"narration": "ナレーション文", "caption": "画面表示用の短い文", "image_query": "English search term for a historical image"}}
  ]
}}
"""


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of an LLM response."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"LLM returned no JSON object:\n{text[:500]}")
    return json.loads(text[start : end + 1])


def generate_script(topic: str, n_scenes: int, cfg: Config) -> Script:
    provider = (cfg.llm_provider or "none").lower()
    prompt = _PROMPT_TEMPLATE.format(topic=topic, n=n_scenes)

    if provider == "anthropic":
        import anthropic  # lazy import
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        model = cfg.llm_model or "claude-sonnet-4-6"
        msg = client.messages.create(
            model=model, max_tokens=2000, system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return Script.from_dict(_extract_json(text))

    if provider == "openai":
        from openai import OpenAI  # lazy import
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        model = cfg.llm_model or "gpt-4o-mini"
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": _SYSTEM},
                      {"role": "user", "content": prompt}],
        )
        return Script.from_dict(_extract_json(resp.choices[0].message.content or ""))

    raise RuntimeError(
        "llm_provider='none': 自動生成にはAPIキーが必要です。\n"
        "  - config.yaml で llm_provider を 'anthropic' か 'openai' に設定し、"
        "対応するAPIキーを環境変数に入れてください。\n"
        "  - または台本JSONを用意して `--script your.json` で渡してください "
        "(例: scripts/sample_sengoku.json)。"
    )
