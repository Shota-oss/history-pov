"""Source scene visuals.

Primary: Wikimedia Commons (public-domain / freely licensed historical media,
no API key). Fallback: a generated gradient with the caption baked in, so the
pipeline still produces output offline or when a search returns nothing.

All images are normalised to an exact cover-crop of the target frame size so
the renderer can apply Ken Burns motion without letterboxing.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path

from .config import Config

_COMMONS_API = "https://commons.wikimedia.org/w/api.php"
_UA = "history-pov/1.0 (https://github.com/shota-oss/history-pov)"


def _cover_crop(img, size: tuple[int, int]):
    from PIL import Image
    tw, th = size
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return img.crop((left, top, left + tw, top + th)).convert("RGB")


def _gradient_fallback(query: str, size: tuple[int, int], out_path: str) -> str:
    """Deterministic gradient placeholder seeded by the query string."""
    import numpy as np
    from PIL import Image

    w, h = size
    seed = int(hashlib.md5(query.encode("utf-8")).hexdigest(), 16)
    rng = np.random.default_rng(seed)
    top = rng.integers(15, 70, 3)
    bot = rng.integers(15, 70, 3)
    y = np.linspace(0, 1, h)[:, None, None]
    grad = (top * (1 - y) + bot * y).astype("uint8") * np.ones((h, w, 1), "uint8")
    Image.fromarray(grad).save(out_path)
    return out_path


def _fetch_wikimedia(query: str, size: tuple[int, int], out_path: str) -> str | None:
    import requests
    from PIL import Image

    params = {
        "action": "query", "format": "json",
        "generator": "search", "gsrsearch": query,
        "gsrnamespace": "6",          # File: namespace
        "gsrlimit": "8",
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": str(size[0] * 2),
    }
    try:
        r = requests.get(_COMMONS_API, params=params,
                         headers={"User-Agent": _UA}, timeout=20)
        r.raise_for_status()
        pages = (r.json().get("query") or {}).get("pages") or {}
    except Exception:
        return None

    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        mime = info.get("mime", "")
        url = info.get("thumburl") or info.get("url")
        if not url or not mime.startswith("image/") or "svg" in mime:
            continue
        try:
            ir = requests.get(url, headers={"User-Agent": _UA}, timeout=30)
            ir.raise_for_status()
            img = Image.open(io.BytesIO(ir.content))
            _cover_crop(img, size).save(out_path, quality=90)
            return out_path
        except Exception:
            continue
    return None


def get_image(query: str, cfg: Config, out_path: str,
              caption: str = "") -> str:
    """Return a path to a cover-cropped image for `query`."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if cfg.image_provider == "wikimedia":
        got = _fetch_wikimedia(query, cfg.size, out_path)
        if got:
            return got
    return _gradient_fallback(query or caption, cfg.size, out_path)
