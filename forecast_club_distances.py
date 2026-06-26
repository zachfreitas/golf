"""Per-club distance reference — measured on-course p80 from Arccos where
available, forecast for the rest. Anchored to your real on-course 7-iron
performance, not range carry.

Why p80? Arccos's "Smart Distance" is roughly the 80th percentile of recent
shots — what you can expect to hit on a well-struck strike, not the median
which gets dragged down by mis-hits. That's what golfers actually plan club
selection around.

Why "last 12 months"? Clubs come and go (you removed a 5-wood, sensors
re-pair). Older shots include retired clubs and pre-improvement performance.
12 months captures your current bag and current skill.

Inputs:
  - ~/golf-data/shots.csv  (Arccos sync output)
  - Book1.xlsx             (your current bag — source of truth for what clubs
                            should appear in the output)

Outputs:
  - per_club_on_course.csv — one row per club in your current bag
  - console table
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from arccos import load_arccos

# -- Calibration ------------------------------------------------------------
# Lookback window for "current" performance (rounds older than this are
# excluded — they may contain retired clubs / pre-improvement strokes).
LOOKBACK_MONTHS = 12

# Minimum shots required per club before its measured p80 is trusted.
# 5 is the smallest sample that yields a reasonably stable 80th percentile
# (lower than that and one outlier swings the number heavily).
MIN_SHOTS_FOR_MEASURED = 5

# Your measured GC3 7-iron carry (range, ideal conditions). Used as a
# secondary reference column so you can see range-vs-course delta.
GC3_7I_CARRY_YD = 127.0

# Arccos label -> Book1 bag abbreviation. Verified against sensor history
# and distance ranges (Club 35's p80 is 168 yd which lines up with the 19°
# 3-hybrid; "Hybrid" tagged is shorter at 156, lines up with the 22° 4H).
ARCCOS_TO_BAG = {
    "Driver":         "Dr",
    "3 Wood":         "3w",
    "Club 35":        "3h",
    "Hybrid":         "4h",
    "5 Iron":         "5i",
    "6 Iron":         "6i",
    "7 Iron":         "7i",
    "8 Iron":         "8i",
    "9 Iron":         "9i",
    "Pitching Wedge": "PW",
    # Wedges (GW/SW/LW) lumped under generic "Wedge" tag — we can't
    # disambiguate them from Arccos shot distance alone, so they fall
    # through to the forecast path below.
}

# Standard amateur-male club-speed delta from 7-iron (mph). Used only for
# clubs the user has in the bag but Arccos can't measure or disambiguate.
DELTA_FROM_7I = {
    "Dr":  +10.0, "3w":  +7.0,  "3h":  +6.0,  "4h":  +4.0,
    "5i":  +5.0,  "6i":  +3.0,  "7i":   0.0,  "8i":  -2.5,
    "9i":  -5.0,  "PW":  -7.0,  "GW": -10.0,  "SW": -12.0,  "LW": -14.0,
}

# Empirical TOTAL-distance coefficient (yd per mph of club speed). Includes
# typical roll/bounce on tee + fairway lies. Calibrated against amateur-male
# Arccos distributions, then scaled by per-user efficiency calibrated to
# their actual 7i performance.
TOTAL_COEFF = {
    "Dr": 2.55, "3w": 2.40, "3h": 2.15, "4h": 2.00,
    "5i": 1.92, "6i": 1.85, "7i": 1.78, "8i": 1.70, "9i": 1.60,
    "PW": 1.50, "GW": 1.30, "SW": 1.10, "LW": 0.90,
}


def measured_p80() -> dict[str, tuple[float, int]]:
    """Compute last-12-month p80 distance per Arccos club label.

    Returns mapping bag_abbr -> (p80_yd, n_shots) for clubs with enough data.
    """
    d = load_arccos()
    s = d.shots.copy()
    s["date"] = pd.to_datetime(s["date"], errors="coerce")
    s = s.dropna(subset=["date"])
    cutoff = s["date"].max() - pd.DateOffset(months=LOOKBACK_MONTHS)
    s = s[(s["date"] >= cutoff)
          & ~s["is_putt"].astype(bool)
          & (s["shot_distance_yd"] > 0)]

    out: dict[str, tuple[float, int]] = {}
    for arccos_label, bag_abbr in ARCCOS_TO_BAG.items():
        grp = s[s["club"] == arccos_label]
        if len(grp) >= MIN_SHOTS_FOR_MEASURED:
            out[bag_abbr] = (round(grp["shot_distance_yd"].quantile(0.8), 0),
                             len(grp))
    return out


def main() -> None:
    measured = measured_p80()

    # Anchor: user's actual on-course 7-iron p80, falling back to GC3 if
    # Arccos doesn't have 10+ recent 7-iron shots.
    anchor_p80 = measured.get("7i", (GC3_7I_CARRY_YD, 0))[0]
    anchor_speed = 74.8  # measured 7i club speed from GC3 sessions
    efficiency = anchor_p80 / (anchor_speed * TOTAL_COEFF["7i"])

    bag = pd.read_excel("Book1.xlsx")[
        ["Club Abbriation", "Club", "Loft"]
    ].rename(columns={"Club Abbriation": "abbr"})
    bag["loft_deg"] = bag["Loft"].astype(str).apply(
        lambda s: float(re.search(r"(\d+\.?\d*)", s).group(1))
    )

    rows = []
    for _, r in bag.iterrows():
        abbr = r["abbr"]
        if abbr not in DELTA_FROM_7I:
            continue

        if abbr in measured:
            p80, n = measured[abbr]
            source = f"Arccos last {LOOKBACK_MONTHS}mo (n={n})"
        else:
            speed = anchor_speed + DELTA_FROM_7I[abbr]
            p80 = round(speed * TOTAL_COEFF[abbr] * efficiency, 0)
            source = "forecast"

        gc3 = GC3_7I_CARRY_YD if abbr == "7i" else None
        delta = (gc3 - p80) if gc3 is not None else None

        rows.append({
            "Club": f"{abbr} ({r['loft_deg']:g} deg)",
            "On-course p80 (yd)": int(p80),
            "Source": source,
            "GC3 carry (yd)": int(gc3) if gc3 is not None else "",
            "Range vs course": f"{int(delta):+d}" if delta is not None else "",
        })

    out = pd.DataFrame(rows)

    # Gap to next-shorter club (carry diff between consecutive bag positions).
    out["Gap to next (yd)"] = ""
    for i in range(len(out) - 1):
        gap = out.iloc[i]["On-course p80 (yd)"] - out.iloc[i + 1]["On-course p80 (yd)"]
        flag = ""
        if gap < 6:
            flag = "  [TIGHT]"
        elif gap > 18:
            flag = "  [WIDE]"
        out.at[i, "Gap to next (yd)"] = f"{int(gap):>3d}{flag}"

    print(f"\n=== ON-COURSE p80 DISTANCES (last {LOOKBACK_MONTHS} months) ===")
    print(f"Anchored to 7i p80 = {anchor_p80:.0f} yd @ {anchor_speed} mph")
    print(f"  Efficiency factor: {efficiency:.3f} (vs amateur-male average 1.000)")
    print()
    print(out.to_string(index=False))

    print("\nGap interpretation:")
    print("  6-15 yd  = healthy spacing")
    print("  <6 yd    = TIGHT (clubs do same job)")
    print("  >18 yd   = WIDE (gap between clubs is hard to play)\n")

    out.to_csv("per_club_on_course.csv", index=False)
    print("Saved: per_club_on_course.csv")


if __name__ == "__main__":
    main()
