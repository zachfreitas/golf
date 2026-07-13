"""Repeatable pipeline: download + parse every per-brand GolfWorks Maltby PDF listed
under "MPF Ratings Sorted by Manufacturer".

These per-brand PDFs are much richer than the master "sorted by score" chart -- they
contain the full engineering breakdown for every iron head:

    Brand | Model | Year | Head Wt (g) | Dimension | VCOG | MOI | RCOG | Loft |
    Adjusted VCOG | VCOG C.F. | C.F. | C.F. | Points | MPF | Category

That means real per-model LOFT, MOI and CG data -- ideal for fitting work.

Repeatability (per user request):
  * The brand list comes from the master manifest (built by build_maltby_mpf_dataset.py),
    which itself detects newly-added brand PDFs on the index page.
  * Each brand PDF is downloaded only when its bytes change (SHA-256 tracked per file).
  * PDFs are cached under data/irons_research/brand_pdfs/ (git-ignored); only the derived
    CSV + hash manifest are versioned.

Usage:
    python scripts/build_maltby_brand_specs.py           # update changed brand PDFs
    python scripts/build_maltby_brand_specs.py --force    # re-download + re-parse all
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "irons_research"
PDF_CACHE = DATA_DIR / "brand_pdfs"
MASTER_MANIFEST = DATA_DIR / "maltby_mpf_manifest.json"
BRAND_MANIFEST = DATA_DIR / "maltby_brand_specs_manifest.json"
OUT_CSV = DATA_DIR / "maltby_mpf_brand_specs.csv"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) golf-analysis-pipeline/1.0"

# --- column layout of the per-brand tables (x-anchor ranges, in PDF points) --------
# (field, x_lo, x_hi, kind)  kind: text | num | year | cat
COLUMNS = [
    ("brand",         0,   185, "text"),
    ("model",       185,   268, "text"),
    ("year",        268,   294, "year"),
    ("head_weight_g", 294, 316, "num"),
    ("dimension",   316,   340, "num"),
    ("vcog",        340,   370, "num"),
    ("moi",         370,   402, "num"),
    ("rcog",        402,   431, "num"),
    ("loft",        431,   458, "num"),
    ("adj_vcog",    458,   488, "num"),
    ("vcog_cf",     488,   520, "num"),
    ("cf_1",        520,   547, "num"),
    ("cf_2",        547,   568, "num"),
    ("points",      568,   591, "num"),
    ("mpf",         591,   616, "num"),
    ("category",    616, 99999, "cat"),
]
CSV_FIELDS = [c[0] for c in COLUMNS] + ["iron_number", "source_pdf"]
ROW_BAND = 18.0  # +/- points around a year anchor (row pitch is ~82pt, so safe)


def _col_for_x(x: float) -> str | None:
    for name, lo, hi, _ in COLUMNS:
        if lo <= x < hi:
            return name
    return None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _iron_number(model: str) -> str:
    import re
    m = re.search(r"#\s*(\d+)", model)
    if m:
        return m.group(1)
    if re.search(r"\bhybrid\b", model, re.I):
        return "hybrid"
    return ""


def load_brand_urls() -> dict[str, str]:
    if not MASTER_MANIFEST.exists():
        raise SystemExit("run build_maltby_mpf_dataset.py first (need brand list).")
    manifest = json.loads(MASTER_MANIFEST.read_text())
    urls = manifest.get("brand_pdfs")
    if not urls:
        raise SystemExit("no brand_pdfs in master manifest; re-run build_maltby_mpf_dataset.py.")
    return urls


def download_brand(label: str, url: str, prev: dict,
                   force: bool) -> tuple[Path, dict, bool]:
    """Download a brand PDF only if changed. Returns (path, validators, changed).

    Checks for updates BEFORE downloading using conditional GET (If-None-Match /
    If-Modified-Since); falls back to a SHA-256 comparison of the fetched bytes.
    """
    safe = label.replace(" ", "_").replace("/", "_")
    path = PDF_CACHE / f"MPF_{safe}.pdf"
    parts = urllib.parse.urlsplit(url)
    enc = urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, urllib.parse.quote(parts.path), parts.query, parts.fragment))

    req = urllib.request.Request(enc, headers={"User-Agent": UA})
    if not force and path.exists():
        if prev.get("etag"):
            req.add_header("If-None-Match", prev["etag"])
        if prev.get("last_modified"):
            req.add_header("If-Modified-Since", prev["last_modified"])

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            validators = {"sha256": _sha256(data),
                          "etag": resp.headers.get("ETag"),
                          "last_modified": resp.headers.get("Last-Modified")}
    except urllib.error.HTTPError as exc:
        if exc.code == 304 and path.exists():  # Not Modified
            return path, prev, False
        raise

    if not force and validators["sha256"] == prev.get("sha256") and path.exists():
        return path, {**prev, **{k: v for k, v in validators.items() if v}}, False

    path.write_bytes(data)
    return path, validators, True


def _is_int(tok: str) -> bool:
    tok = tok.strip()
    return bool(tok) and (tok.lstrip("-").isdigit())


def parse_brand_pdf(path: Path) -> list[dict]:
    doc = fitz.open(path)
    _mpf_lo, _mpf_hi = COLUMNS[-2][1], COLUMNS[-2][2]  # MPF column x-range
    out: list[dict] = []
    for page in doc:
        words = page.get_text("words")
        # Anchor each row on its MPF value: an integer inside the MPF column. MPF is
        # always present (even when the year is "-"), so this catches every data row.
        anchors = [w for w in words
                   if _mpf_lo <= w[0] < _mpf_hi and _is_int(w[4])]
        for a in anchors:
            ay = a[1]
            band = [w for w in words if abs(w[1] - ay) <= ROW_BAND]
            buckets: dict[str, list] = {}
            for w in band:
                col = _col_for_x(w[0])
                if col:
                    buckets.setdefault(col, []).append(w)

            rec: dict[str, object] = {}
            for name, _lo, _hi, kind in COLUMNS:
                toks = sorted(buckets.get(name, []), key=lambda w: (round(w[1]), w[0]))
                text = " ".join(t[4] for t in toks).strip()
                if kind in ("text", "cat"):
                    rec[name] = text
                elif kind == "year":
                    # 4-digit year or "-" (unknown); take the year-column token.
                    rec[name] = toks[0][4] if toks else ""
                else:  # num -- keep first numeric-looking token
                    rec[name] = toks[0][4] if toks else ""

            if not rec.get("brand") or not rec.get("model"):
                continue
            rec["iron_number"] = _iron_number(str(rec["model"]))
            rec["source_pdf"] = path.name
            out.append(rec)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    PDF_CACHE.mkdir(parents=True, exist_ok=True)
    urls = load_brand_urls()
    manifest = json.loads(BRAND_MANIFEST.read_text()) if BRAND_MANIFEST.exists() else {}
    validators = manifest.get("validators", {})

    all_rows: list[dict] = []
    changed_ct = 0
    per_brand_counts: dict[str, int] = {}

    for label in sorted(urls):
        try:
            path, v, changed = download_brand(
                label, urls[label], validators.get(label, {}), args.force)
        except Exception as exc:
            print(f"[{label}] download FAILED: {exc}")
            continue
        validators[label] = v
        changed_ct += int(changed)
        rows = parse_brand_pdf(path)
        per_brand_counts[label] = len(rows)
        all_rows.extend(rows)
        flag = "updated" if changed else "cached"
        print(f"[{label:18}] {flag:7} -> {len(rows):4} rows")

    # Write combined CSV (sorted by MPF desc where numeric).
    def mpf_key(r):
        try:
            return -float(r["mpf"])
        except (ValueError, TypeError):
            return 1e9
    all_rows.sort(key=mpf_key)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(all_rows)

    manifest = {
        "validators": validators,
        "brands": len(per_brand_counts),
        "total_rows": len(all_rows),
        "per_brand_counts": per_brand_counts,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    BRAND_MANIFEST.write_text(json.dumps(manifest, indent=2))

    print(f"\n{changed_ct} brand PDF(s) changed this run.")
    print(f"wrote {len(all_rows)} detailed rows from {len(per_brand_counts)} brands "
          f"-> {OUT_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
