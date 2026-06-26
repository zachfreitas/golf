"""Per-club distance reference for your CURRENT BAG.

Source priority:
  1. **Arccos Smart Distance** (from `_cache_raw/clubs_v6.json`) — the
     authoritative number Arccos itself displays in the app. Derived from
     well-struck shots only; this is what you should plan club selection
     around, not raw shot medians.
  2. **Recent on-course p80** from last-12-month shots, as a sanity check.
  3. **Forecast** only for clubs without Arccos data (fallback only).

Inputs (read via arccos.load_arccos):
  - ~/golf-data/_cache_raw/clubs_v6.json   (paired bag, Smart Distance)
  - ~/golf-data/shots.csv                  (recent on-course p80 cross-check)
  - Book1.xlsx                              (loft + make/model reference)

Outputs:
  - per_club_on_course.csv — one row per club currently in your bag
  - console table with gap diagnostics
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from arccos import load_arccos

# -- Configuration ----------------------------------------------------------
LOOKBACK_MONTHS = 12          # window for the p80 cross-check column
MIN_SHOTS_FOR_P80 = 5         # below this, p80 is too noisy to show

# Gap thresholds (yards) for the diagnostic column.
GAP_TIGHT_MAX = 6             # < this many yards = clubs overlap in practice
GAP_WIDE_MIN = 18             # > this many yards = hole in the bag

# Reference: your GC3-measured 7-iron range carry. Used purely for the
# "Range vs course" delta column on the 7i row — not used to forecast
# anything anymore.
GC3_7I_CARRY_YD = 127.0


def recent_p80_per_label(data, months: int = LOOKBACK_MONTHS) -> dict:
    """Map shots.csv `club` label -> (p80_yd, n_shots) for last N months.

    Filters to shots.shots_in_bag() so retired-club shots don't sneak in.
    """
    s = data.shots_in_bag()
    s = s[~s["is_putt"].astype(bool) & (s["shot_distance_yd"] > 0)].copy()
    s["date"] = pd.to_datetime(s["date"], errors="coerce")
    s = s.dropna(subset=["date"])
    if s.empty:
        return {}
    cutoff = s["date"].max() - pd.DateOffset(months=months)
    s = s[s["date"] >= cutoff]
    out: dict[str, tuple[float, int]] = {}
    for label, grp in s.groupby("club"):
        if len(grp) >= MIN_SHOTS_FOR_P80:
            out[label] = (round(grp["shot_distance_yd"].quantile(0.8), 0),
                          len(grp))
    return out


def main() -> None:
    data = load_arccos()
    if data.paired_bag.empty:
        raise SystemExit(
            "No paired bag found at "
            f"{data.store / '_cache_raw' / 'clubs_v6.json'}.\n"
            "Re-run the Arccos puller (`python ~/tools/golf-reports/setup.py`) "
            "so the raw cache is populated."
        )

    bag = data.paired_bag.copy()
    p80 = recent_p80_per_label(data)

    # Layer the recent-shots cross-check onto the authoritative bag. Match
    # via shots_csv_label (the puller's label) because shots.csv uses the
    # puller's labels, not our user-friendly display overrides.
    bag["p80_recent_yd"] = bag["shots_csv_label"].map(
        lambda lbl: p80.get(lbl, (None, 0))[0]
    )
    bag["p80_recent_n"] = bag["shots_csv_label"].map(
        lambda lbl: p80.get(lbl, (None, 0))[1]
    )

    # Drop the putter row from distance analysis.
    bag = bag[~bag["label"].str.contains("Putter", na=False)].copy()

    # Distance gap to next-shorter club.
    bag = bag.sort_values("smart_distance_yd", ascending=False).reset_index(drop=True)
    bag["gap_to_next_yd"] = bag["smart_distance_yd"].diff(-1).round(1)

    def flag_gap(g):
        if pd.isna(g):
            return ""
        if g < 0:
            return f"{int(g):+d}  [REVERSED]"
        if g < GAP_TIGHT_MAX:
            return f"{int(g):>3d}  [TIGHT]"
        if g > GAP_WIDE_MIN:
            return f"{int(g):>3d}  [WIDE]"
        return f"{int(g):>3d}"

    def as_int(x):
        return "" if pd.isna(x) else f"{int(round(x))}"

    out = pd.DataFrame({
        "Club": bag["label"],
        "Make/Model": (bag["make"].fillna("") + " " + bag["model"].fillna("")).str.strip(),
        "Smart Distance (yd)": bag["smart_distance_yd"].apply(as_int),
        "Longest (yd)": bag["longest_yd"].apply(as_int),
        "Recent p80 (yd)": bag["p80_recent_yd"].apply(as_int),
        "n (last 12mo)": bag["p80_recent_n"].apply(as_int),
        "Gap to next (yd)": bag["gap_to_next_yd"].apply(flag_gap),
    })

    # Compute one diagnostic: where does the bag have problems?
    problems = []
    for i, row in bag.iterrows():
        g = row["gap_to_next_yd"]
        if pd.isna(g): continue
        next_label = bag.iloc[i + 1]["label"] if i + 1 < len(bag) else "?"
        if g < 0:
            problems.append(
                f"  REVERSED: {row['label']} ({row['smart_distance_yd']:.0f} yd) "
                f"is SHORTER than the next club {next_label} "
                f"({bag.iloc[i + 1]['smart_distance_yd']:.0f} yd)")
        elif g < GAP_TIGHT_MAX:
            problems.append(
                f"  TIGHT:    {row['label']} -> {next_label} only {g:.0f} yd apart")
        elif g > GAP_WIDE_MIN:
            problems.append(
                f"  WIDE:     {row['label']} -> {next_label} is {g:.0f} yd "
                f"(consider what fits between)")

    print("\n=== CURRENT BAG — per-club distances ===")
    print(f"Store: {data.store}")
    print(f"Source: Arccos Smart Distance (authoritative); recent p80 = last "
          f"{LOOKBACK_MONTHS}mo cross-check\n")
    print(out.to_string(index=False))

    if problems:
        print("\nGap diagnostics:")
        for p in problems:
            print(p)
    else:
        print("\nGap diagnostics: no tight overlaps or wide gaps detected.")

    # 7i reference vs range. Note: Smart Distance is on-course TOTAL (carry
    # + roll/bounce), GC3 is range CARRY. They are not directly comparable;
    # typical iron roll-out is 5-10 yd, so Smart - 7 ≈ on-course carry.
    seven = bag[bag["label"] == "7 Iron"]
    if not seven.empty:
        sd = seven.iloc[0]["smart_distance_yd"]
        if sd:
            est_course_carry = sd - 7  # rough iron roll-out
            print(f"\nReference: 7i Smart Distance {sd:.0f} yd (total, on-course) "
                  f"≈ {est_course_carry:.0f} yd carry. GC3 range carry: "
                  f"{GC3_7I_CARRY_YD:.0f} yd. Course-vs-range delta: "
                  f"{est_course_carry - GC3_7I_CARRY_YD:+.0f} yd.")

    # Wedges share the generic "Wedge" label in shots.csv, so the recent p80
    # column can't disambiguate them. The Smart Distance column is per-club.
    wedge_count = bag[bag["label"] == "Wedge"].shape[0]
    if wedge_count > 1:
        print(f"\nNote: your {wedge_count} wedges share the generic 'Wedge' "
              "label in shots.csv, so the 'Recent p80' column shows the "
              "same total-wedge p80 for each. Trust Smart Distance for "
              "per-wedge planning.")

    out.to_csv("per_club_on_course.csv", index=False)
    print("\nSaved: per_club_on_course.csv")


if __name__ == "__main__":
    main()
