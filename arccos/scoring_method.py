"""Will Robins Scoring Method — Level 1 analysis over Arccos data.

Level 1 = the 100-yard scoring zone. Two questions per hole:
  1. How many strokes did it take to get inside 100 yd? (strokes_to_zone)
  2. How many strokes from inside 100 to holed?          (strokes_in_zone)

Robins' promise: if you keep the ball in play AND achieve "down in three
from 100" (strokes_in_zone <= 3), your worst score on any hole is a bogey.
Bogey golf on every hole = ~90 on a par-72 = mid-teens handicap floor.

The math per par:
  par 3: zone in <= 1 stroke  + <= 3 in zone = <= 4 = bogey ceiling
  par 4: zone in <= 2 strokes + <= 3 in zone = <= 5 = bogey ceiling
  par 5: zone in <= 3 strokes + <= 3 in zone = <= 6 = bogey ceiling
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

ZONE_YARDS = 100
DOWN_IN_TARGET = 3

# strokes_to_zone target for "reached zone in regulation" (=par score if D3)
ZONE_REG_TARGET = {3: 1, 4: 1, 5: 2}

# strokes_to_zone ceiling for "bogey ceiling met" (Robins' promise)
ZONE_BOGEY_CEILING = {3: 1, 4: 2, 5: 3}

# ── Level ladder (Robins L1-L4) ─────────────────────────────────────────────
# Level = fixed distance-to-pin baseline reached in "GIR-style" par-2 strokes.
# All four levels use the SAME reg-target (par-2), so achievement nests:
# L4 ⊂ L3 ⊂ L2 ⊂ L1 (a hole where you hit GIR also cleared inside-100).
LEVEL_YARDS   = {1: 100, 2: 50, 3: 25}  # L4 handled specially (GIR via putts)
LEVEL_REG_TARGET = {3: 1, 4: 2, 5: 3}   # par - 2

# ── Gear inference (heuristic proxy for shot intent) ────────────────────────
# True Robins gears are the shot-by-shot INTENT chosen before the swing —
# Arccos does not record intent. This heuristic buckets non-putt shots by
# start-distance-to-pin as a directional proxy. Putts are tallied separately.
def infer_gear(start_dist_yd: float) -> str:
    """Bucket a non-putt shot into G1-G4 by start distance to pin.

    G4  full-swing long shot (driver / 3W / long approach)
    G3  mid-iron / hybrid approach (attack L3 target)
    G2  wedge scoring shot (attack L2 target)
    G1  chip / pitch (attack L1 matrix / safe position)

    G0 (recovery / punch-out) is not inferrable from distance alone and is
    reported as a separate 'penalty-hole recovery' proxy in aggregate.
    """
    if start_dist_yd is None or pd.isna(start_dist_yd):
        return "G?"
    if start_dist_yd > 180:
        return "G4"
    if start_dist_yd > 100:
        return "G3"
    if start_dist_yd > 30:
        return "G2"
    return "G1"


def select_last_n_rounds(rounds: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Return the n most recent rounds by date, newest first."""
    return (rounds
            .sort_values("date", ascending=False)
            .head(n)
            .reset_index(drop=True))


def compute_hole_metrics(
    shots: pd.DataFrame,
    holes: pd.DataFrame,
    round_ids: list[int],
) -> pd.DataFrame:
    """Per-hole Level 1 metrics for the given rounds.

    Returns one row per hole with columns:
      round_id, date, course, hole_id, par, shots, score_to_par, putts,
      penalties, in_play, strokes_to_zone, strokes_in_zone,
      zone_reached_in_reg, down_in_3, bogey_ceiling_met, blow_up
    """
    h = holes[holes["round_id"].isin(round_ids)].copy()
    s = shots[shots["round_id"].isin(round_ids)].copy()

    # Non-putt shots that STARTED outside the 100-yd zone are "to-zone" strokes.
    # Putts are always inside the zone by definition.
    s["is_to_zone_stroke"] = (
        (~s["is_putt"].astype(bool))
        & (s["start_dist_to_pin_yd"] > ZONE_YARDS)
    )
    to_zone = (s.groupby(["round_id", "hole_id"])["is_to_zone_stroke"]
                .sum()
                .rename("strokes_to_zone")
                .reset_index())

    m = h.merge(to_zone, on=["round_id", "hole_id"], how="left")
    m["strokes_to_zone"] = m["strokes_to_zone"].fillna(0).astype(int)
    m["strokes_in_zone"] = (m["shots"] - m["strokes_to_zone"]).clip(lower=0).astype(int)

    m["in_play"] = (m["penalties"].fillna(0) == 0).astype(int)
    m["down_in_3"] = (m["strokes_in_zone"] <= DOWN_IN_TARGET).astype(int)

    m["zone_reg_target"] = m["par"].map(ZONE_REG_TARGET)
    m["bogey_ceiling_target"] = m["par"].map(ZONE_BOGEY_CEILING)
    m["zone_reached_in_reg"] = (m["strokes_to_zone"] <= m["zone_reg_target"]).astype(int)
    m["bogey_ceiling_met"] = (
        (m["strokes_to_zone"] <= m["bogey_ceiling_target"])
        & (m["down_in_3"] == 1)
    ).astype(int)
    m["blow_up"] = (m["score_to_par"] >= 2).astype(int)

    return m[[
        "round_id", "date", "course", "hole_id", "par", "shots", "score_to_par",
        "putts", "penalties", "in_play", "strokes_to_zone", "strokes_in_zone",
        "zone_reached_in_reg", "down_in_3", "bogey_ceiling_met", "blow_up",
    ]].sort_values(["date", "round_id", "hole_id"]).reset_index(drop=True)


def format_scorecard_df(hole_metrics: pd.DataFrame) -> pd.DataFrame:
    """Robins-style scorecard: one row per hole, human-readable Y/N."""
    def yn(x):
        return "Y" if x == 1 else "N"

    out = hole_metrics.copy()
    out["In Play"] = out["in_play"].map(yn)
    out["Zone Reg"] = out["zone_reached_in_reg"].map(yn)
    out["D3"] = out["down_in_3"].map(yn)
    out["Bogey Ceiling"] = out["bogey_ceiling_met"].map(yn)
    return out.rename(columns={
        "hole_id": "Hole",
        "par": "Par",
        "shots": "Score",
        "score_to_par": "+/-",
        "strokes_to_zone": "To Zone",
        "strokes_in_zone": "In Zone",
        "putts": "Putts",
        "penalties": "Pen",
    })[[
        "Hole", "Par", "Score", "+/-", "In Play", "To Zone", "In Zone",
        "Zone Reg", "D3", "Bogey Ceiling", "Putts", "Pen",
    ]]


@dataclass
class SummaryStats:
    n_rounds: int
    n_holes: int
    total_score: int
    total_par: int
    total_to_par: int
    in_play_pct: float
    zone_reg_pct: float
    d3_rate: float
    bogey_ceiling_pct: float
    blow_up_count: int
    blow_up_pct: float
    avg_putts_per_hole: float
    by_par: pd.DataFrame  # index = par, columns = per-par breakdown

    def to_frame(self) -> pd.DataFrame:
        """Flat headline table for display."""
        return pd.DataFrame([
            ("Rounds",                 f"{self.n_rounds}"),
            ("Holes played",           f"{self.n_holes}"),
            ("Score vs par (total)",   f"{self.total_score} / {self.total_par}  (+{self.total_to_par})"),
            ("In-play %",              f"{self.in_play_pct:.0%}"),
            ("Zone reached in reg %",  f"{self.zone_reg_pct:.0%}"),
            ("Down-in-3 rate",         f"{self.d3_rate:.0%}   <-- HEADLINE"),
            ("Bogey-ceiling %",        f"{self.bogey_ceiling_pct:.0%}"),
            ("Blow-up holes (dbl+)",   f"{self.blow_up_count} of {self.n_holes}  ({self.blow_up_pct:.0%})"),
            ("Avg putts / hole",       f"{self.avg_putts_per_hole:.2f}"),
        ], columns=["Metric", "Value"])


def aggregate_summary(hole_metrics: pd.DataFrame) -> SummaryStats:
    """Roll per-hole metrics up to a Level 1 dashboard."""
    n_holes = len(hole_metrics)
    n_rounds = hole_metrics["round_id"].nunique()

    by_par = (hole_metrics
              .groupby("par")
              .agg(holes=("hole_id", "count"),
                   avg_score=("shots", "mean"),
                   in_play_pct=("in_play", "mean"),
                   zone_reg_pct=("zone_reached_in_reg", "mean"),
                   d3_rate=("down_in_3", "mean"),
                   bogey_ceiling_pct=("bogey_ceiling_met", "mean"),
                   avg_to_zone=("strokes_to_zone", "mean"),
                   avg_in_zone=("strokes_in_zone", "mean"),
                   avg_putts=("putts", "mean"),
                   blow_up_pct=("blow_up", "mean"))
              .round(2))

    return SummaryStats(
        n_rounds=n_rounds,
        n_holes=n_holes,
        total_score=int(hole_metrics["shots"].sum()),
        total_par=int(hole_metrics["par"].sum()),
        total_to_par=int(hole_metrics["score_to_par"].sum()),
        in_play_pct=hole_metrics["in_play"].mean(),
        zone_reg_pct=hole_metrics["zone_reached_in_reg"].mean(),
        d3_rate=hole_metrics["down_in_3"].mean(),
        bogey_ceiling_pct=hole_metrics["bogey_ceiling_met"].mean(),
        blow_up_count=int(hole_metrics["blow_up"].sum()),
        blow_up_pct=hole_metrics["blow_up"].mean(),
        avg_putts_per_hole=hole_metrics["putts"].mean(),
        by_par=by_par,
    )


def score_if_bogey_ceiling_held(hole_metrics: pd.DataFrame) -> pd.DataFrame:
    """For each round: actual vs 'if you had achieved bogey ceiling on every hole'.

    The counterfactual is: par if bogey_ceiling_met, else par+1 (bogey).
    This IS the Robins promise made numeric.
    """
    hm = hole_metrics.copy()
    hm["ceiling_score"] = hm["par"] + (1 - hm["bogey_ceiling_met"])  # 0 over = par, 1 over = bogey
    # Actual score capped at ceiling too — you can't "gain" by playing worse than bogey
    # on a hole where ceiling was met. But when ceiling was met, actual <= bogey by construction.
    return (hm.groupby(["round_id", "date", "course"])
              .agg(holes=("hole_id", "count"),
                   par=("par", "sum"),
                   actual=("shots", "sum"),
                   ceiling=("ceiling_score", "sum"))
              .reset_index()
              .assign(strokes_saved=lambda d: d["actual"] - d["ceiling"])
              .sort_values("date"))


def derive_practice_priorities(agg: SummaryStats) -> list[str]:
    """Heuristic Level 1 practice-priority read from the summary.

    Rules of thumb (Robins' framing):
      * D3 < 50% → the leak is INSIDE 100 yd. Split further by putts/hole.
      * Zone-reg < 50% → the leak is GETTING TO 100 yd. Full-swing problem.
      * In-play < 85% → penalty strokes are killing rounds; conservative
        club-off-the-tee is higher ROI than any technique work.
      * blow-up % > 20% → mindset/reset: after any bad shot, revert to a
        lower-level target (e.g. from GIR intent → get-to-100 intent).
    """
    notes = []
    if agg.in_play_pct < 0.85:
        notes.append(
            f"IN-PLAY LEAK: {agg.in_play_pct:.0%} of holes penalty-free "
            f"(target >=85%). Highest-ROI fix: club down off the tee on any "
            f"hole where trouble is in range. Not a swing problem -- a "
            f"decision problem."
        )
    if agg.zone_reg_pct < 0.60:
        notes.append(
            f"GET-TO-ZONE LEAK: only {agg.zone_reg_pct:.0%} of holes reached "
            f"100 yd in regulation. Full-swing distance/direction is the "
            f"gate -- practice range with target commitment, not the short-"
            f"game area."
        )
    if agg.d3_rate < 0.50:
        notes.append(
            f"DOWN-IN-3 LEAK: {agg.d3_rate:.0%} D3 rate is the biggest single "
            f"stroke bleed. Split diagnosis: if avg putts/hole > 2.0, the "
            f"leak is on the green; if putts ~ 2.0 but D3 still low, the "
            f"leak is chip/pitch proximity."
        )
        if agg.avg_putts_per_hole > 2.0:
            notes.append(
                f"  -> Putting sub-leak confirmed: {agg.avg_putts_per_hole:.2f} "
                f"putts/hole. Prioritize 5-15 ft putts."
            )
        else:
            notes.append(
                f"  -> Chip/pitch sub-leak: putts/hole ~ tour-average, so D3 "
                f"failures are landing you >15 ft on chips. Practice "
                f"proximity control from 20-50 yd."
            )
    if agg.blow_up_pct > 0.20:
        notes.append(
            f"BLOW-UP RATE: {agg.blow_up_pct:.0%} of holes are dbl+ "
            f"(target <=15%). On-course rule for next round: after any bad "
            f"shot, drop your target one level (Level 4 GIR intent -> Level "
            f"1 get-inside-100 intent). Kill the compounding."
        )
    if not notes:
        notes.append(
            "No single leak dominates -- Level 1 fundamentals look solid. "
            "Time to graduate to Level 2 (inside 50 yd) analysis."
        )
    return notes


# ── Level ladder ────────────────────────────────────────────────────────────
def compute_level_ladder(
    shots: pd.DataFrame,
    holes: pd.DataFrame,
    round_ids: list[int],
) -> pd.DataFrame:
    """Per-hole achievement of Robins Levels 1-4.

    L1/L2/L3 = ball first ended inside 100/50/25 yd on shot ≤ par-2.
    L4 (GIR) = non-putt shot count ≤ par-2 AND at least one putt taken
              (proxy: ball reached green by regulation stroke).

    Returns columns:
      round_id, hole_id, date, course, par,
      l1_reg, l2_reg, l3_reg, l4_reg   (0/1 flags)
    """
    h = holes[holes["round_id"].isin(round_ids)].copy()
    s = shots[shots["round_id"].isin(round_ids)].copy()

    non_putt = s[~s["is_putt"].astype(bool)].copy()
    non_putt["shot_num"] = (
        non_putt.sort_values(["round_id", "hole_id"])
                .groupby(["round_id", "hole_id"]).cumcount() + 1
    )

    # For each level 1/2/3: first shot where end_dist <= level yd threshold.
    first_reach = {}
    for lvl, yd in LEVEL_YARDS.items():
        reached = (non_putt[non_putt["end_dist_to_pin_yd"] <= yd]
                    .groupby(["round_id", "hole_id"])["shot_num"]
                    .min()
                    .rename(f"first_shot_l{lvl}"))
        first_reach[lvl] = reached

    # L4 = GIR proxy: (non_putt count <= par-2) AND (>=1 putt)
    np_count = (non_putt.groupby(["round_id", "hole_id"])
                        .size().rename("np_count"))
    putt_count = (s[s["is_putt"].astype(bool)]
                    .groupby(["round_id", "hole_id"])
                    .size().rename("putt_count"))

    m = h.merge(first_reach[1], on=["round_id", "hole_id"], how="left")
    m = m.merge(first_reach[2], on=["round_id", "hole_id"], how="left")
    m = m.merge(first_reach[3], on=["round_id", "hole_id"], how="left")
    m = m.merge(np_count, on=["round_id", "hole_id"], how="left")
    m = m.merge(putt_count, on=["round_id", "hole_id"], how="left")

    m["np_count"] = m["np_count"].fillna(0).astype(int)
    m["putt_count"] = m["putt_count"].fillna(0).astype(int)
    m["reg_target"] = m["par"].map(LEVEL_REG_TARGET)

    def flag(col, target):
        return ((m[col].notna()) & (m[col] <= target)).astype(int)

    m["l1_reg"] = flag("first_shot_l1", m["reg_target"])
    m["l2_reg"] = flag("first_shot_l2", m["reg_target"])
    m["l3_reg"] = flag("first_shot_l3", m["reg_target"])
    m["l4_reg"] = ((m["np_count"] <= m["reg_target"])
                   & (m["putt_count"] >= 1)).astype(int)

    return m[[
        "round_id", "hole_id", "date", "course", "par",
        "l1_reg", "l2_reg", "l3_reg", "l4_reg",
    ]].sort_values(["date", "round_id", "hole_id"]).reset_index(drop=True)


def summarise_level_ladder(ladder: pd.DataFrame) -> pd.DataFrame:
    """Aggregate ladder to counts + percentages per level."""
    total_holes = len(ladder)
    rows = []
    for lvl, label in [(1, "L1 (inside 100 yd in reg)"),
                       (2, "L2 (inside 50 yd in reg)"),
                       (3, "L3 (inside 25 yd in reg)"),
                       (4, "L4 / GIR (on green in reg)")]:
        col = f"l{lvl}_reg"
        n = int(ladder[col].sum())
        rows.append({
            "Level": f"L{lvl}",
            "Definition": label,
            "Holes achieved": f"{n} / {total_holes}",
            "Rate": f"{n / total_holes:.0%}" if total_holes else "n/a",
        })
    return pd.DataFrame(rows)


# ── Gear tally (inferred) ───────────────────────────────────────────────────
def compute_gear_tally(
    shots: pd.DataFrame,
    round_ids: list[int],
) -> pd.DataFrame:
    """Inferred Gear tally G1-G4 for non-putt shots + separate putt count.

    Heuristic: bucket by start_dist_to_pin_yd (see infer_gear docstring).
    NOT a measure of intent — it's a distance-band proxy. A punch-out from
    150 yd will be tagged G3 even though the intent was G0 recovery.
    """
    s = shots[shots["round_id"].isin(round_ids)].copy()
    non_putt = s[~s["is_putt"].astype(bool)].copy()
    non_putt["gear"] = non_putt["start_dist_to_pin_yd"].apply(infer_gear)

    counts = non_putt["gear"].value_counts().reindex(
        ["G4", "G3", "G2", "G1", "G?"], fill_value=0
    )
    putt_n = int(s["is_putt"].astype(bool).sum())

    rows = [
        ("G4", "Long full swing / driver / 3W  (start >180 yd)",       int(counts["G4"])),
        ("G3", "Mid iron / hybrid approach     (100-180 yd)",          int(counts["G3"])),
        ("G2", "Wedge / scoring full swing     (30-100 yd)",           int(counts["G2"])),
        ("G1", "Chip / pitch / short shot      (≤30 yd, non-putt)",    int(counts["G1"])),
        ("G0", "Recovery / punch-out           (not inferrable — 0)",  0),
        ("Putt", "On-green stroke              (separate category)",   putt_n),
    ]
    df = pd.DataFrame(rows, columns=["Gear", "Definition (inferred by start distance)", "Shots"])
    total_shots = df["Shots"].sum()
    df["Rate"] = df["Shots"].apply(
        lambda n: f"{n / total_shots:.0%}" if total_shots else "n/a"
    )
    return df
