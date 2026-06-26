"""Targeted diagnostic analyses on top of Arccos data.

Four functions, one per analysis the Targeted_Diagnostics notebook drives:

  approach_band_deepdive(data, lo=125, hi=150)
      Slice approach shots in a yardage band, summarise by club / lie / wind.
      Default window targets the 125-150 yd leak found in earlier analysis.

  putt_make_by_distance(data, bands=...)
      Make-% per putt-distance band, with shot count and Tour benchmark.
      First-putt-only: subsequent putts on the same hole are excluded so
      tap-ins don't inflate the short-band numbers.

  lie_penalty_matrix(data)
      Per-club Smart Distance by lie (tee / fairway / rough / sand). Derived
      from clubs.csv terrain columns. Shows what missing the fairway costs.

  twin_oaks_hole_heatmap(data, course_name="Twin Oaks GC")
      Per-hole average score-to-par and SG contribution at your most-played
      course. Identifies nemesis holes vs scoring opportunities.

All functions return DataFrames sized for direct display in a notebook.
Plotting is left to the caller so the diagnostics module stays render-free.
"""
from __future__ import annotations

import pandas as pd

# Roughly PGA Tour averages for make %, used as the benchmark overlay in
# putt_make_by_distance. Source: Mark Broadie published putting stats.
TOUR_MAKE_PCT = {
    "0-3 ft": 99, "3-5 ft": 88, "5-8 ft": 58, "8-12 ft": 33,
    "12-18 ft": 17, "18-25 ft": 8, "25-35 ft": 4, "35+ ft": 2,
}
PUTT_BAND_BINS = [0, 3, 5, 8, 12, 18, 25, 35, 999]
PUTT_BAND_LABELS = list(TOUR_MAKE_PCT.keys())


def approach_band_deepdive(data, lo: float = 125, hi: float = 150) -> dict:
    """Slice approach shots in [lo, hi] yd. Returns dict of summary tables."""
    s = data.shots_in_bag()
    s = s[(s["category_approx"] == "approach")
          & s["start_dist_to_pin_yd"].between(lo, hi)
          & s["sg_shot_approx"].notna()].copy()

    # Join round-level weather + map to display labels.
    bag = data.paired_bag.set_index("shots_csv_label")
    label_map = bag["label"].to_dict()
    s["display_club"] = s["club"].map(lambda c: label_map.get(c, c))

    rounds_weather = data.rounds[["round_id", "wind_mph", "wind_dir", "temp_f"]]
    s = s.merge(rounds_weather, on="round_id", how="left")

    # By club
    by_club = (s.groupby("display_club")
               .agg(shots=("sg_shot_approx", "size"),
                    avg_sg=("sg_shot_approx", "mean"),
                    median_proximity_ft=("end_dist_to_pin_yd",
                                         lambda x: x.median() * 3))
               .round(2).sort_values("shots", ascending=False))

    # By lie
    by_lie = (s.groupby("lie_approx")
              .agg(shots=("sg_shot_approx", "size"),
                   avg_sg=("sg_shot_approx", "mean"))
              .round(2).sort_values("shots", ascending=False))

    # By wind bucket
    s["wind_bucket"] = pd.cut(s["wind_mph"], bins=[0, 5, 10, 15, 99],
                              labels=["calm <5", "5-10", "10-15", "15+"],
                              include_lowest=True)
    by_wind = (s.groupby("wind_bucket", observed=True)
               .agg(shots=("sg_shot_approx", "size"),
                    avg_sg=("sg_shot_approx", "mean"))
               .round(2))

    return {
        "by_club": by_club,
        "by_lie": by_lie,
        "by_wind": by_wind,
        "n_total": len(s),
        "total_sg_lost": round(s["sg_shot_approx"].sum(), 1),
    }


def putt_make_by_distance(data) -> pd.DataFrame:
    """Make-% per first-putt distance band, vs PGA Tour benchmark."""
    s = data.shots
    putts = s[s["is_putt"].astype(bool)].copy()
    # Filter out Arccos's phantom 0-distance "putts" — these are logging
    # artifacts where the ball was already at the hole; they distort the
    # short-putt make-% calculation.
    putts = putts[putts["start_dist_to_pin_yd"] > 0.2]
    # Keep first putt per (round, hole) only — distance to pin at start.
    first = (putts.sort_values(["round_id", "hole_id", "shot_num"])
             .groupby(["round_id", "hole_id"]).first().reset_index())
    # Putt distance is measured in feet in Arccos (start_dist_to_pin_yd
    # holds yards; convert by ×3).
    first["distance_ft"] = first["start_dist_to_pin_yd"] * 3
    first["band"] = pd.cut(first["distance_ft"], bins=PUTT_BAND_BINS,
                           labels=PUTT_BAND_LABELS, right=False)

    # A first putt is "made" iff it's the only putt on the hole.
    putts_per_hole = (putts.groupby(["round_id", "hole_id"])["shot_num"].count()
                     .reset_index().rename(columns={"shot_num": "n_putts"}))
    first = first.merge(putts_per_hole, on=["round_id", "hole_id"])
    first["made"] = (first["n_putts"] == 1).astype(int)

    summary = (first.groupby("band", observed=True)
               .agg(attempts=("made", "size"),
                    makes=("made", "sum"))
               .reset_index())
    summary["band"] = summary["band"].astype(str)  # drop categorical for arithmetic
    summary["make_pct"] = (summary["makes"] / summary["attempts"] * 100).round(1)
    summary["tour_pct"] = summary["band"].map(TOUR_MAKE_PCT)
    summary["gap_vs_tour"] = (summary["make_pct"] - summary["tour_pct"]).round(1)
    return summary


def lie_penalty_matrix(data) -> pd.DataFrame:
    """Per-club Smart Distance by lie. Penalty = lie distance - fairway distance.

    Pulls from clubs.csv terrain columns, filtered to currently-paired clubs.
    Wedges are disambiguated by smart_distance since they share the generic
    'Wedge' label.
    """
    paired_ids = set(data.paired_bag["shots_csv_label"].dropna().tolist())
    c = data.clubs[data.clubs["club"].isin(paired_ids)].copy()

    cols = ["tee_yd", "fairway_yd", "rough_yd", "sand_yd"]
    have = [col for col in cols if col in c.columns]

    # Build display label. For unique club labels, use the bag's friendly
    # label. For shared labels (the 3 wedges), append smart_distance so
    # they're distinguishable.
    bag_counts = data.paired_bag["shots_csv_label"].value_counts()
    label_lookup = data.paired_bag.drop_duplicates(
        "shots_csv_label", keep="first").set_index("shots_csv_label")["label"]

    def _display(row):
        lbl = row["club"]
        friendly = label_lookup.get(lbl, lbl)
        if bag_counts.get(lbl, 0) > 1:
            sd = row.get("smart_distance_yd")
            return f"{friendly} ({sd:.0f} yd)" if pd.notna(sd) else friendly
        return friendly

    c["display_club"] = c.apply(_display, axis=1)

    # For non-duplicate labels, keep only the highest-usage row (in case
    # the puller emitted multiple sensor rows). For duplicates (wedges),
    # keep all rows since each row is a distinct sensor.
    c = c.sort_values("usage_count", ascending=False)
    c["is_dup_label"] = c["club"].map(bag_counts).fillna(0) > 1
    unique_rows = c[~c["is_dup_label"]].drop_duplicates("club", keep="first")
    dup_rows = c[c["is_dup_label"]].drop_duplicates("display_club", keep="first")
    c = pd.concat([unique_rows, dup_rows])

    out = c[["display_club"] + have + ["usage_count"]].copy()
    out = out.rename(columns={
        "tee_yd": "From tee (yd)",
        "fairway_yd": "From fairway (yd)",
        "rough_yd": "From rough (yd)",
        "sand_yd": "From sand (yd)",
        "usage_count": "n shots",
    })
    if "From fairway (yd)" in out.columns and "From rough (yd)" in out.columns:
        out["Rough penalty (yd)"] = (out["From fairway (yd)"]
                                     - out["From rough (yd)"]).round(0)
    return out.sort_values("From tee (yd)", ascending=False, na_position="last")


def twin_oaks_hole_heatmap(data, course_name: str = "Twin Oaks GC") -> pd.DataFrame:
    """Per-hole avg score-to-par + SG contribution at your most-played course.

    Pulls from data.round_dash[rid]['overall']['holeScores'] across all
    rounds matching the course name. holes.csv would also work but the
    dash data is per-round which makes the average easier to compute.
    """
    rounds_at_course = data.rounds[
        data.rounds["course"].fillna("").str.contains(course_name, case=False, regex=False)
    ]
    rids = rounds_at_course["round_id"].tolist()

    rows = []
    for rid in rids:
        dash = data.round_dash.get(int(rid)) or data.round_dash.get(rid)
        if not dash:
            continue
        for hs in dash.get("overall", {}).get("holeScores", []) or []:
            rows.append({
                "round_id": rid,
                "hole_id": hs.get("holeId"),
                "par": hs.get("par"),
                "shots": hs.get("noOfShots"),
                "net_score": hs.get("netScore"),  # score relative to par
            })
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    summary = (df.groupby("hole_id")
               .agg(rounds=("round_id", "nunique"),
                    par=("par", "first"),
                    avg_score=("shots", "mean"),
                    avg_to_par=("net_score", "mean"),
                    worst_to_par=("net_score", "max"),
                    best_to_par=("net_score", "min"))
               .round(2).sort_index())
    summary["bleed_rank"] = summary["avg_to_par"].rank(ascending=False).astype(int)
    return summary
