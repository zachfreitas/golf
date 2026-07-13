"""Repeatable fetcher for Cool Clubs iron review data.

Cool Clubs publishes its robot/CT measurements as .webp image cards
(e.g. Callaway-Quantum-Iron-Key-Data.webp). This script:
  * discovers every manufacturer review page from https://coolclubs.com/reviews/
  * pulls each page and collects the IRON data-card image URLs
    (Key-Data + Sci-Data; also Graph/Scan for reference)
  * downloads the full-resolution .webp and converts to PNG (for visual extraction)
  * is repeatable: per-image SHA-256 in a manifest; only changed images re-downloaded

The numeric data lives inside the images, so a follow-up step (vision-capable agents)
reads the PNGs and extracts the tables. This script just gets the pixels locally.

Usage:
    python scripts/fetch_coolclubs_iron_data.py           # update changed images
    python scripts/fetch_coolclubs_iron_data.py --force
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "irons_research" / "coolclubs"
PNG_DIR = OUT_DIR / "png"
MANIFEST = OUT_DIR / "coolclubs_manifest.json"

REVIEWS_URL = "https://coolclubs.com/reviews/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36 golf-analysis/1.0"

# Brands that actually make irons (skip putter/shaft/grip-only review pages).
IRON_BRANDS = {"callaway", "cobra", "mizuno", "ping", "pxg", "srixon",
               "taylormade", "titleist", "wilson", "epon", "cc-compare"}
# Data cards hold the numbers. Filenames don't reliably say "Iron" (e.g. Mizuno "M13-M15"
# are irons, TaylorMade "QI" is a driver), so grab all data/graph cards and let the
# vision step keep only irons. Skip obvious non-iron model tokens where we can.
WANT = re.compile(r"(Key-Data|Sci-Data|Graph|Graphing)", re.I)
COMPARE = re.compile(r"(Iron|Compar|Key-Data|Graph)", re.I)
# Drop cards whose filename clearly names a driver/fairway/hybrid/putter (not an iron).
NON_IRON = re.compile(r"(Driver|Fairway|-FW|Hybrid|Putter|Wedge|Ball|Shaft|Grip|logo)", re.I)


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def brand_pages() -> dict[str, str]:
    html = get(REVIEWS_URL).decode("utf-8", "replace")
    pages = {}
    for m in re.findall(r'href="(https://coolclubs\.com/reviews-([a-z0-9-]+)/)"', html):
        url, slug = m
        if slug in IRON_BRANDS:
            pages[slug] = url
    return pages


def iron_webps(page_html: str, slug: str) -> set[str]:
    urls = set()
    pat = COMPARE if slug == "cc-compare" else WANT
    for u in re.findall(r'https://coolclubs\.com/wp-content/uploads/[0-9/]+[^"\s]+\.webp', page_html):
        u = u.split(" ")[0]              # strip srcset width tokens
        if "-768x432" in u or "-300x" in u or "x60" in u:
            continue                      # skip thumbnails; keep full-res
        fn = u.rsplit("/", 1)[-1]
        if pat.search(fn) and not NON_IRON.search(fn):
            urls.add(u)
    return urls


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    PNG_DIR.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    hashes = manifest.get("hashes", {})

    pages = brand_pages()
    print(f"[discover] {len(pages)} iron-relevant review pages: {', '.join(sorted(pages))}")

    total, changed = 0, 0
    index: dict[str, list[str]] = {}
    for slug, url in sorted(pages.items()):
        try:
            html = get(url).decode("utf-8", "replace")
        except Exception as exc:
            print(f"[{slug}] page fetch failed: {exc}")
            continue
        imgs = sorted(iron_webps(html, slug))
        index[slug] = []
        for iu in imgs:
            fn = iu.rsplit("/", 1)[-1]
            png_name = f"{slug}__{fn.rsplit('.',1)[0]}.png"
            png_path = PNG_DIR / png_name
            try:
                data = get(iu)
            except Exception as exc:
                print(f"  [{slug}] {fn} download failed: {exc}")
                continue
            h = hashlib.sha256(data).hexdigest()
            total += 1
            index[slug].append(png_name)
            if not args.force and hashes.get(png_name) == h and png_path.exists():
                continue
            # convert webp bytes -> png
            tmp = PNG_DIR / (png_name + ".webp")
            tmp.write_bytes(data)
            Image.open(tmp).convert("RGB").save(png_path)
            tmp.unlink()
            hashes[png_name] = h
            changed += 1
        print(f"[{slug:12}] {len(imgs)} iron images")

    MANIFEST.write_text(json.dumps({
        "hashes": hashes, "index": index,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=2))
    print(f"\n{total} iron images found, {changed} downloaded/updated -> {PNG_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
