"""Repeatable pipeline: download + parse the GolfWorks Maltby Playability Factor (MPF)
iron ratings chart into a clean CSV.

Source: https://www.golfworks.com/head-mpf-ratings/  (master chart, "Sorted by Score")
The chart is the authoritative Maltby Playability Factor database covering every major
iron brand/model/year with a single "playability" score and a category band.

Key features (per user request: "make this process repeatable and check for pdf
updates before downloading"):
  * Conditional download -- uses HTTP ETag / Last-Modified and a SHA-256 hash stored in
    a manifest. The PDF is only re-downloaded + re-parsed when GolfWorks actually
    changes it. Run it any time; it is a no-op when nothing changed.
  * Coordinate-based PDF parsing (PyMuPDF) that handles the 2-column layout, multi-word
    brands (TOMMY ARMOUR, POWER BILT, 1 IRON GOLF ...), category section banners,
    negative MPF scores, and missing ("-") years.
  * Category is taken from the printed section banners (authoritative), and independently
    cross-checked against Maltby's published MPF score bands as a verification step.

Usage:
    python scripts/build_maltby_mpf_dataset.py            # update if changed
    python scripts/build_maltby_mpf_dataset.py --force    # force re-download + re-parse
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF

# --------------------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "irons_research"
PDF_PATH = DATA_DIR / "MPFRatingsChart.pdf"
CSV_PATH = DATA_DIR / "maltby_mpf_irons.csv"
MANIFEST_PATH = DATA_DIR / "maltby_mpf_manifest.json"

INDEX_URL = "https://www.golfworks.com/head-mpf-ratings/"
MASTER_URL = "https://www.golfworks.com/content/PDFs/Head_MPFs/MPFRatingsChart.pdf"
BASE_URL = "https://www.golfworks.com/content/PDFs/Head_MPFs/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) golf-analysis-pipeline/1.0"

# --------------------------------------------------------------- category handling
# Printed section banners in the chart, normalized -> clean label.
CATEGORY_BANNERS = {
    "ULTRA GAME IMPROVEMENT": "Ultra Game Improvement",
    "SUPER GAME IMPROVEMENT": "Super Game Improvement",
    "GAME IMPROVEMENT": "Game Improvement",
    "CONVENTIONAL": "Conventional",
    "CLASSIC": "Classic",
    "PLAYERS CLASSIC": "Players Classic",
}

# Maltby's published MPF score bands -- used ONLY to cross-check the banner-derived
# category (the chart is globally sorted by score, so score alone implies the band).
def category_from_score(mpf: int) -> str:
    if mpf >= 851:
        return "Ultra Game Improvement"
    if mpf >= 701:
        return "Super Game Improvement"
    if mpf >= 551:
        return "Game Improvement"
    if mpf >= 401:
        return "Conventional"
    if mpf >= 251:
        return "Classic"
    return "Players Classic"


# ------------------------------------------------------------------- download step
def _conditional_download(url: str, manifest: dict) -> tuple[bytes | None, dict]:
    """Return (pdf_bytes or None if unchanged, response_meta)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if manifest.get("etag"):
        req.add_header("If-None-Match", manifest["etag"])
    if manifest.get("last_modified"):
        req.add_header("If-Modified-Since", manifest["last_modified"])
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            meta = {
                "etag": resp.headers.get("ETag"),
                "last_modified": resp.headers.get("Last-Modified"),
                "content_length": resp.headers.get("Content-Length"),
            }
            return data, meta
    except urllib.error.HTTPError as exc:
        if exc.code == 304:  # Not Modified
            return None, {}
        raise


def ensure_pdf(force: bool = False) -> tuple[bool, dict]:
    """Download the PDF if it changed. Returns (changed, manifest)."""
    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())

    if force:
        manifest = {}  # ignore cached validators

    data, meta = _conditional_download(MASTER_URL, manifest)

    if data is None:
        print("[download] server reports 304 Not Modified -- PDF unchanged.")
        return False, manifest

    new_hash = hashlib.sha256(data).hexdigest()
    if not force and new_hash == manifest.get("sha256") and PDF_PATH.exists():
        print("[download] downloaded bytes match cached hash -- PDF unchanged.")
        # refresh validators in case they rotated
        manifest.update({k: v for k, v in meta.items() if v})
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
        return False, manifest

    PDF_PATH.write_bytes(data)
    manifest = {
        "url": MASTER_URL,
        "sha256": new_hash,
        "bytes": len(data),
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **{k: v for k, v in meta.items() if v},
    }
    print(f"[download] PDF changed/new -- saved {len(data):,} bytes ({new_hash[:12]}...).")
    return True, manifest


# ----------------------------------------------------- brand-pdf discovery (index)
def discover_brand_pdfs(manifest: dict) -> dict:
    """Fetch the index page and diff the per-brand PDF links against what we saw last
    time, so we notice when GolfWorks ADDS a new manufacturer to the database.

    Returns manifest updated with a 'brand_pdfs' map {brand_label: url}. Prints any
    newly appeared or removed brands.
    """
    req = urllib.request.Request(INDEX_URL, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            html = resp.read().decode("utf-8", "replace")
    except Exception as exc:  # network hiccup shouldn't break the whole pipeline
        print(f"[brands] could not fetch index page ({exc}); skipping brand-diff.")
        return manifest

    # Links look like ../content/PDFs/Head_MPFs/MPF_CALLAWAY.pdf
    found: dict[str, str] = {}
    for href in re.findall(r'href=["\']([^"\']*MPF_[^"\']+\.pdf)["\']', html, re.I):
        filename = href.split("/")[-1]
        # Brand label = filename minus the "MPF_" prefix and ".pdf" suffix.
        label = re.sub(r"^MPF_", "", filename, flags=re.I)
        label = re.sub(r"\.pdf$", "", label, flags=re.I).replace("%20", " ").strip()
        url = urllib.parse.urljoin(BASE_URL, filename)
        found[label] = url

    prev = manifest.get("brand_pdfs", {})
    new_brands = sorted(set(found) - set(prev))
    gone_brands = sorted(set(prev) - set(found))

    print(f"[brands] {len(found)} per-brand PDFs listed on index page.")
    if prev:
        if new_brands:
            print(f"[brands] *** NEW brand PDF(s) since last run: {', '.join(new_brands)}")
        if gone_brands:
            print(f"[brands] brand PDF(s) no longer listed: {', '.join(gone_brands)}")
        if not new_brands and not gone_brands:
            print("[brands] no change in brand list.")
    else:
        print("[brands] first run -- recording brand list as baseline.")

    manifest["brand_pdfs"] = found
    manifest["brand_pdfs_checked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return manifest


# ---------------------------------------------------------------------- pdf parser
COL_SPLIT = 306.0          # page midpoint: x0 < split => left column
LEFT_MODEL_X = 115.0       # words left of this in the left col are the brand
RIGHT_BRAND_START = 306.0
RIGHT_MODEL_X = 391.0
YEAR_RE = re.compile(r"^\d{4}$")
DASH_CHARS = {"-", "–", "—", "‒"}


def _cluster_rows(words: list) -> list[list]:
    """Group words sharing a text baseline (y0) into rows, sorted top->bottom."""
    rows: dict[int, list] = {}
    for w in words:
        key = round(w[1])  # y0; all words in a printed row share the same baseline
        rows.setdefault(key, []).append(w)
    ordered = []
    for key in sorted(rows):
        ordered.append(sorted(rows[key], key=lambda w: w[0]))
    return ordered


def _normalize_header(text: str) -> str:
    text = re.sub(r"\(.*?\)", "", text)          # drop "(continued . . .)"
    text = re.sub(r"[^A-Z ]", " ", text.upper())  # keep letters/spaces only
    return re.sub(r"\s+", " ", text).strip()


def _parse_row(row: list, model_x: float) -> dict | None:
    """Turn one clustered row of words into a record, or None if not a data row."""
    tokens = [w[4] for w in row]
    if len(tokens) < 3:
        return None

    mpf_tok = tokens[-1]
    year_tok = tokens[-2]

    # MPF must be an integer (may be negative).
    try:
        mpf = int(mpf_tok)
    except ValueError:
        return None

    # Year must be a 4-digit number or a dash (unknown).
    if YEAR_RE.match(year_tok):
        year = int(year_tok)
    elif year_tok in DASH_CHARS:
        year = None
    else:
        return None

    brand_words = [w[4] for w in row if w[0] < model_x]
    middle_words = [w[4] for w in row[:-2] if w[0] >= model_x]
    if not brand_words or not middle_words:
        return None

    brand = " ".join(brand_words).strip()
    model = " ".join(middle_words).strip()
    # Guard against banner/title lines that slip through.
    if brand in {"BRAND", "MALTBY PLAYABILITY", "MAJOR"}:
        return None
    return {"brand": brand, "model": model, "year": year, "mpf": mpf}


def _iron_number(model: str) -> str:
    m = re.search(r"#\s*(\d+)", model)
    if m:
        return m.group(1)
    if re.search(r"\bhybrid\b", model, re.I):
        return "hybrid"
    return ""


def parse_pdf(pdf_path: Path) -> tuple[list[dict], str]:
    doc = fitz.open(pdf_path)
    records: list[dict] = []
    current_category = None
    updated_label = ""

    for page in doc:
        words = page.get_text("words")
        for side, (lo, hi, model_x) in {
            "L": (0.0, COL_SPLIT, LEFT_MODEL_X),
            "R": (COL_SPLIT, 9999.0, RIGHT_MODEL_X),
        }.items():
            col_words = [w for w in words if lo <= w[0] < hi]
            for row in _cluster_rows(col_words):
                joined = " ".join(w[4] for w in row)

                # Track the "Updated M/YY" version label.
                if "Updated" in joined:
                    m = re.search(r"Updated\s+([\d/]+)", joined)
                    if m:
                        updated_label = m.group(1)

                # Category banner?
                norm = _normalize_header(joined)
                if norm in CATEGORY_BANNERS:
                    current_category = CATEGORY_BANNERS[norm]
                    continue

                rec = _parse_row(row, model_x)
                if rec is None:
                    continue
                rec["category"] = current_category
                rec["category_by_score"] = category_from_score(rec["mpf"])
                rec["iron_number"] = _iron_number(rec["model"])
                rec["source"] = "GolfWorks Maltby Playability Factor"
                records.append(rec)

    return records, updated_label


# ----------------------------------------------------------------------- csv write
import csv

CSV_FIELDS = ["brand", "model", "year", "mpf", "category",
              "category_by_score", "iron_number", "source"]


def write_csv(records: list[dict], path: Path) -> None:
    records = sorted(records, key=lambda r: (-r["mpf"], r["brand"], r["model"]))
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in records:
            writer.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in CSV_FIELDS})


# ---------------------------------------------------------------------- verify
def verify(records: list[dict]) -> None:
    print("\n===== VERIFICATION =====")
    print(f"total irons parsed: {len(records)}")

    from collections import Counter
    cats = Counter(r["category"] for r in records)
    for cat in CATEGORY_BANNERS.values():
        print(f"  {cat:<24} {cats.get(cat, 0)}")
    missing_cat = [r for r in records if r["category"] is None]
    if missing_cat:
        print(f"  !! {len(missing_cat)} rows with NO category (first: {missing_cat[0]})")

    # Cross-check banner category vs score-band category.
    mismatched = [r for r in records if r["category"] != r["category_by_score"]]
    print(f"category banner vs score-band mismatches: {len(mismatched)}")
    for r in mismatched[:8]:
        print(f"    {r['brand']} {r['model']} ({r['year']}) mpf={r['mpf']}"
              f" banner={r['category']} score={r['category_by_score']}")

    # Spot-check the user's clubs.
    print("\n-- user's clubs of interest --")
    needles = [("CALLAWAY", "X-20 Tour"), ("CALLAWAY", "X-22 Tour"),
               ("TAYLORMADE", "P770")]
    for brand, frag in needles:
        hits = [r for r in records if r["brand"] == brand and frag.lower() in r["model"].lower()]
        for r in sorted(hits, key=lambda r: -(r["year"] or 0)):
            print(f"    {r['brand']:<11} {r['model']:<28} {r['year']}  MPF={r['mpf']}  [{r['category']}]")


# ---------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="force re-download and re-parse")
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    changed, manifest = ensure_pdf(force=args.force)

    # Always check the index page for newly-added (or removed) brand PDFs.
    manifest = discover_brand_pdfs(manifest)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    if not changed and CSV_PATH.exists() and not args.force:
        print(f"[parse] master chart unchanged; existing CSV kept at {CSV_PATH.relative_to(ROOT)}")
        return 0

    if not PDF_PATH.exists():
        print("[error] no PDF available to parse.", file=sys.stderr)
        return 1

    records, updated_label = parse_pdf(PDF_PATH)
    write_csv(records, CSV_PATH)

    manifest["pdf_updated_label"] = updated_label
    manifest["parsed_rows"] = len(records)
    manifest["parsed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    print(f"[parse] chart version label: 'Updated {updated_label}'")
    print(f"[parse] wrote {len(records)} rows -> {CSV_PATH.relative_to(ROOT)}")
    verify(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
