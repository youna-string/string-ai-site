#!/usr/bin/env python3
"""Publishable website derivatives of the approved store posters; no upload.

Usage: python3 scripts/sync-store-images.py [--app-dir ../string-ai-app]
Requires the existing local Pillow runtime with WebP support. Source PNGs are
read-only. This script owns assets/screenshots and the generated image map.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PANELS = ("lesson", "mission", "piece", "progress", "habit", "library")
WIDTHS = (432, 864)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-dir", type=Path, default=ROOT.parent / "string-ai-app")
    args = parser.parse_args()
    app = args.app_dir.resolve()
    output = ROOT / "assets/screenshots"
    output.mkdir(parents=True, exist_ok=True)
    mapping: dict = {}
    sources: dict = {}
    keep: set[Path] = set()

    for lang in ("en", "ko"):
        mapping[lang] = {}
        for index, panel in enumerate(PANELS, 1):
            source = app / f"store-assets/screenshots/out/play-phone/{lang}/{index:02}_{panel}.png"
            raw = source.read_bytes()
            with Image.open(io.BytesIO(raw)) as image:
                if image.size != (1080, 1920):
                    raise ValueError(f"Expected portrait 1080×1920: {source}")
                variants = []
                for width in WIDTHS:
                    height = width * 16 // 9
                    if width > image.width or width * image.height != height * image.width:
                        raise ValueError("Source aspect ratio and no-upscale contract failed")
                    buffer = io.BytesIO()
                    image.convert("RGB").resize((width, height), Image.Resampling.LANCZOS).save(
                        buffer, "WEBP", quality=90, method=6
                    )
                    data = buffer.getvalue()
                    dest = output / f"{panel}-{lang}-{width}.{sha(data)[:12]}.webp"
                    dest.write_bytes(data)
                    keep.add(dest)
                    variants.append((dest.relative_to(ROOT).as_posix(), width))
                mapping[lang][panel] = {
                    "src": variants[-1][0],
                    "srcset": ", ".join(f"{name} {width}w" for name, width in variants),
                }
            sources[f"{lang}/{panel}"] = {
                "path": source.relative_to(app).as_posix(), "sha256": sha(raw),
                "width": 1080, "height": 1920,
            }

    # The original app icon is also a cacheable shared file, not three data URIs.
    with Image.open(app / "assets/icon.png") as icon:
        if icon.width != icon.height or icon.width < 128:
            raise ValueError("Expected a square native app icon of at least 128px")
        buffer = io.BytesIO()
        icon.resize((128, 128), Image.Resampling.LANCZOS).save(buffer, "PNG", optimize=True)
        data = buffer.getvalue()
    icon_path = output / f"icon.{sha(data)[:12]}.png"
    icon_path.write_bytes(data)
    keep.add(icon_path)
    icon_url = icon_path.relative_to(ROOT).as_posix()

    html_path = ROOT / "index.html"
    html = html_path.read_text()
    html = re.sub(r'(\b(?:src|href)=")(?:data:image/[^\"]+|assets/screenshots/icon\.[^\"]+)(")',
                  lambda m: m[1] + icon_url + m[2], html)

    def replace_img(match: re.Match) -> str:
        tag = match[0]
        panel = re.search(r'data-panel="([^"]+)"', tag)[1]
        shot = mapping["ko"][panel]  # HTML is Korean when JavaScript is unavailable.
        tag = re.sub(r'\s(?:src|srcset)="[^"]*"', '', tag)
        return tag[:-1] + f' src="{shot["src"]}" srcset="{shot["srcset"]}">'

    html, count = re.subn(r'<img\b[^>]*data-panel="[^"]+"[^>]*>', replace_img, html)
    if count != 6:
        raise ValueError(f"Expected six unique screenshot elements, found {count}")
    html, count = re.subn(
        r'/\* STORE_IMAGES_START \*/.*?/\* STORE_IMAGES_END \*/',
        '/* STORE_IMAGES_START */\n  const STORE_IMAGES = ' +
        json.dumps(mapping, ensure_ascii=False, separators=(",", ":")) +
        ';\n  /* STORE_IMAGES_END */', html, flags=re.S,
    )
    if count != 1 or "data:image/" in html:
        raise ValueError("Generated image map or external-image contract failed")
    html_path.write_text(html)
    manifest = {"sourceTarget": "play-phone", "sources": sources,
                "variants": mapping, "icon": icon_url,
                "outputSizes": [[432, 768], [864, 1536]]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    # This directory is generator-owned; stale hashed derivatives are not copies to keep.
    for old in output.iterdir():
        if old.suffix in (".webp", ".png") and old not in keep:
            old.unlink()
    print(f"Generated 24 WebP derivatives + shared icon; 12 source hashes recorded. HTML {len(html.encode()):,} bytes.")


if __name__ == "__main__":
    main()
