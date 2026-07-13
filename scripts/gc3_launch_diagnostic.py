"""GC3 launch-condition diagnostic for Zach's irons.

Question being answered: "I don't think I get enough height, spin, or distance on my
irons for my swing speed / AoA. What's the issue, and would a different VCOG (CG height)
or MOI help?"

Approach:
  * Parse every GC3 iron session (handles the multi-section GC3 CSV export format).
  * Aggregate per club, using a robust median over well-struck shots (drops chunks/thins).
  * Compare his launch conditions to reasonable windows for his measured club speed.
  * Flag deficits in spin / peak height / descent angle (green-holding) and tie them to
    the CG (VCOG) and MOI levers.

Outputs:
  outputs/gc3_launch_diagnostic.csv   (per-club robust launch profile + verdicts)
"""
from __future__ import annotations

import csv
import glob
import re
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
SESS_GLOB = str(ROOT / "data" / "sessions" / "session_summary*.csv")
OUT = ROOT / "outputs" / "gc3_launch_diagnostic.csv"

# GC3 header -> our short field names (matched by substring, case-insensitive).
FIELD_MAP = {
    "Carry": "carry", "Peak Height": "peak_ht", "Descent Angle": "descent",
    "Ball Speed": "ball_spd", "Launch Angle": "launch", "Back Spin": "backspin",
    "Total Spin": "totalspin", "Club Speed at Impact": "club_spd_impact",
    "Club Speed": "club_spd", "Smash Factor": "smash", "Angle of Attack": "aoa",
    "Dynamic Loft": "dyn_loft",
}
IRON_CLUBS = {"3i", "4i", "5i", "6i", "7i", "8i", "9i", "PW"}


def num(cell: str):
    """Pull a signed float from a GC3 cell like '30.9 L', '2.1 DN', '1,610 L'."""
    if cell is None:
        return None
    s = cell.replace(",", "").strip()
    m = re.match(r"[-+]?\d*\.?\d+", s)
    return float(m.group()) if m else None


def parse_session(path: str):
    """Yield (club, list-of-shot-dicts) blocks from one GC3 export."""
    rows = list(csv.reader(open(path, encoding="utf-8")))
    i = 0
    while i < len(rows):
        r = rows[i]
        first = (r[0] if r else "").strip()
        header_next = i + 1 < len(rows) and "Carry" in ",".join(rows[i + 1])
        if first and header_next:
            club = first
            header = rows[i + 1]
            # Map header columns to our field names by substring.
            colidx = {}
            for ci, h in enumerate(header):
                h = (h or "").strip()
                for key, short in FIELD_MAP.items():
                    if h == key:
                        colidx[short] = ci
            shots = []
            j = i + 2
            while j < len(rows):
                rr = rows[j]
                tag = (rr[0] if rr else "").strip()
                if tag == "" and all(c.strip() == "" for c in rr):
                    j += 1
                    continue
                if tag.lower().startswith("average") or not tag.isdigit():
                    break
                shot = {short: num(rr[ci]) for short, ci in colidx.items() if ci < len(rr)}
                shots.append(shot)
                j += 1
            yield club, shots
            i = j
        else:
            i += 1


def robust_profile(shots: list[dict]) -> dict:
    """Median over well-struck shots (drop low-smash / short-carry mishits)."""
    carries = [s["carry"] for s in shots if s.get("carry")]
    if not carries:
        return {}
    cmed = median(carries)
    good = [s for s in shots
            if s.get("carry") and s["carry"] >= 0.85 * cmed
            and (s.get("smash") is None or s["smash"] >= 1.25)]
    good = good or shots
    prof = {"n_all": len(shots), "n_good": len(good)}
    for f in ["club_spd", "ball_spd", "smash", "launch", "backspin", "peak_ht",
              "descent", "aoa", "carry", "dyn_loft"]:
        vals = [s[f] for s in good if s.get(f) is not None]
        prof[f] = round(median(vals), 1) if vals else None
    return prof


# Reasonable launch windows by club at ~72-80 mph club speed (mid handicap, off turf).
# (spin rpm, launch deg, descent deg, peak height in FEET) -- for green-holding flight.
WINDOWS = {
    "5i": dict(backspin=(4300, 5300), descent=(41, 46), peak_ht=(78, 96)),
    "6i": dict(backspin=(4800, 5800), descent=(43, 47), peak_ht=(80, 98)),
    "7i": dict(backspin=(5500, 6800), descent=(45, 50), peak_ht=(82, 100)),
    "8i": dict(backspin=(6500, 7800), descent=(46, 51), peak_ht=(82, 100)),
}


def verdicts(club: str, p: dict) -> str:
    w = WINDOWS.get(club)
    if not w:
        return ""
    out = []
    for metric, (lo, hi) in w.items():
        v = p.get(metric)
        if v is None:
            continue
        if v < lo:
            out.append(f"{metric} LOW ({v} vs {lo}-{hi})")
        elif v > hi:
            out.append(f"{metric} high ({v} vs {lo}-{hi})")
    return "; ".join(out) if out else "in-window"


def main() -> None:
    by_club: dict[str, list[dict]] = {}
    for path in sorted(glob.glob(SESS_GLOB)):
        for club, shots in parse_session(path):
            if club in IRON_CLUBS and shots:
                by_club.setdefault(club, []).extend(shots)

    rows = []
    order = ["3i", "4i", "5i", "6i", "7i", "8i", "9i", "PW"]
    for club in sorted(by_club, key=lambda c: order.index(c) if c in order else 99):
        p = robust_profile(by_club[club])
        p["club"] = club
        p["verdict"] = verdicts(club, p)
        rows.append(p)

    cols = ["club", "n_all", "n_good", "club_spd", "ball_spd", "smash", "launch",
            "backspin", "dyn_loft", "peak_ht", "descent", "aoa", "carry", "verdict"]
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    print(f"wrote {OUT.relative_to(ROOT)}\n")
    hdr = f"{'club':<5}{'n':>4}{'clubMPH':>8}{'ballMPH':>8}{'smash':>7}" \
          f"{'launch':>7}{'spin':>7}{'dynLft':>7}{'peakFt':>7}{'desc':>6}{'AoA':>6}{'carry':>7}"
    print(hdr)
    for r in rows:
        print(f"{r['club']:<5}{r.get('n_good',''):>4}{_s(r,'club_spd'):>8}{_s(r,'ball_spd'):>8}"
              f"{_s(r,'smash'):>7}{_s(r,'launch'):>7}{_s(r,'backspin'):>7}{_s(r,'dyn_loft'):>7}"
              f"{_s(r,'peak_ht'):>7}{_s(r,'descent'):>6}{_s(r,'aoa'):>6}{_s(r,'carry'):>7}")
    print()
    for r in rows:
        if r.get("verdict"):
            print(f"  {r['club']}: {r['verdict']}")


def _s(r, k):
    v = r.get(k)
    return "" if v is None else v


if __name__ == "__main__":
    main()
