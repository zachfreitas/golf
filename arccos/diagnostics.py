"""Targeted diagnostic analyses on top of Arccos + GC3 data.

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

import glob
import re

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


def _signed(val: str | float) -> float | None:
    """Parse GC3 direction-suffixed values like '27.1 R' -> +27.1, '1.2 L' -> -1.2."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    m = re.match(r"(-?\d+\.?\d*)\s*([RL]?)", s)
    if not m:
        return None
    num = float(m.group(1))
    if m.group(2) == "L":
        num = -num
    return num


def load_gc3_sessions(pattern: str = "session_summary*.csv") -> pd.DataFrame:
    """Load all GC3 session CSVs into a unified DataFrame.

    Each CSV has 2 header rows (golfer name + club tag), so we skip them.
    Direction-suffixed numeric columns (Offline, Curve, Launch Direction,
    Side Spin) are parsed into signed floats: Right = +, Left = −.
    """
    files = sorted(glob.glob(pattern))
    if not files:
        return pd.DataFrame()
    frames = []
    for f in files:
        try:
            # FSX export format: line 1 = golfer name + "Shot Analysis",
            # line 2 = blank, line 3 = "<club>,", line 4 = column headers,
            # line 5+ = data. Header row has a leading empty cell for shot
            # number, which produces an "Unnamed: 0" column.
            df = pd.read_csv(f, skiprows=3)
            df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
            df["__session_file"] = f
            frames.append(df)
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    gc = pd.concat(frames, ignore_index=True)
    # Parse direction-suffixed columns into signed floats.
    for col in ("Offline", "Curve", "Launch Direction", "Side Spin"):
        if col in gc.columns:
            gc[col + "_signed"] = gc[col].apply(_signed)
    return gc


def range_vs_course_7i(data, gc3: pd.DataFrame | None = None) -> dict:
    """Compare GC3 range 7-iron distribution to on-course 7-iron from Arccos.

    Returns a dict with stats and the raw distributions ready for plotting.

    Important: GC3 'Carry' is launch-monitor carry distance (no roll).
    Arccos 'shot_distance_yd' is on-course TOTAL distance (carry + roll).
    For irons, roll is typically 5-10 yd; the model-comparable column is
    GC3 'Total' rather than 'Carry'. Both are reported below.
    """
    if gc3 is None:
        gc3 = load_gc3_sessions()

    gc3_carry = gc3["Carry"].dropna() if not gc3.empty else pd.Series([], dtype=float)
    gc3_total = gc3["Total"].dropna() if not gc3.empty else pd.Series([], dtype=float)
    gc3_offline = (gc3["Offline_signed"].dropna()
                   if "Offline_signed" in gc3.columns else pd.Series([], dtype=float))

    # Arccos 7-iron shots — current bag only, recent rounds.
    s = data.shots_in_bag()
    arc_7i = s[(s["club"] == "7 Iron") & (s["shot_distance_yd"] > 0)
               & ~s["is_putt"].astype(bool)]
    arc_dist = arc_7i["shot_distance_yd"].dropna()

    def _stats(series: pd.Series, label: str) -> dict:
        if series.empty:
            return {"label": label, "n": 0}
        return {
            "label": label,
            "n": int(len(series)),
            "mean": round(series.mean(), 1),
            "std": round(series.std(), 1),
            "p20": round(series.quantile(0.2), 1),
            "median": round(series.median(), 1),
            "p80": round(series.quantile(0.8), 1),
            "min": round(series.min(), 1),
            "max": round(series.max(), 1),
        }

    return {
        "gc3_carry_stats": _stats(gc3_carry, "GC3 carry (yd, range, no roll)"),
        "gc3_total_stats": _stats(gc3_total, "GC3 total (yd, range, modeled roll)"),
        "arc_total_stats": _stats(arc_dist, "Arccos total (yd, course)"),
        "gc3_offline_stats": _stats(gc3_offline, "GC3 offline (yd, +R/-L)"),
        "gc3_carry": gc3_carry,
        "gc3_total": gc3_total,
        "gc3_offline": gc3_offline,
        "arc_total": arc_dist,
    }


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
                    avg_to_par=("net_score", "mean"),
                    median_to_par=("net_score", "median"),
                    bogey_or_worse_pct=("net_score", lambda x: (x >= 1).mean() * 100),
                    double_or_worse_pct=("net_score", lambda x: (x >= 2).mean() * 100),
                    par_or_better_pct=("net_score", lambda x: (x <= 0).mean() * 100),
                    worst_to_par=("net_score", "max"),
                    best_to_par=("net_score", "min"))
               .round(1).sort_index())
    # Rank by both average AND median+frequency so we can flag holes where
    # the average understates the typical pain (occasional par drags it down
    # while most rounds are double-bogey or worse — see hole 3 vs hole 1).
    summary["avg_rank"] = summary["avg_to_par"].rank(ascending=False, method="min").astype(int)
    summary["double_rank"] = summary["double_or_worse_pct"].rank(ascending=False, method="min").astype(int)
    # Composite nemesis score: average of the two ranks (lower = worse hole).
    summary["nemesis_rank"] = ((summary["avg_rank"] + summary["double_rank"]) / 2).rank(method="min").astype(int)
    return summary
