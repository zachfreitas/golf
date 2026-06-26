"""Load Arccos data produced by chrisdecali/golf-reports.

Default store: ~/golf-data/ (set by setup.py / GOLF_STORE env var).
Override via load_arccos(store=...).

Surfaces three things:
  - The four flat CSVs (rounds, holes, shots, clubs) produced by the puller.
  - `paired_bag`: currently-in-bag clubs with authoritative Arccos Smart
    Distance, read from `_cache_raw/clubs_v6.json`. The puller's `clubs.csv`
    intermingles paired + unpaired (retired) clubs without distinction, which
    is the main reason the per-club analysis kept turning up phantom 5-woods
    and "Club 16" mysteries. Filter via paired_bag.club_id / label to scope
    to your real current bag.
  - `is_paired_label(label)`: convenience check for whether a shots.csv `club`
    label corresponds to a currently-paired club.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DEFAULT_STORE = Path(os.environ.get("GOLF_STORE") or "~/golf-data").expanduser()

# Puller's clubType -> label map (verbatim from ingest/pull_arccos.py:CLUBTYPE).
# This is what actually appears in shots.csv `club` column. The puller emits
# `f"Club {ct}"` for any clubType it can't name, which is why your 3-hybrid
# (clubType 35) shows up as "Club 35" in shots.csv. Don't add to this — use
# CLUBTYPE_OVERRIDES below for display-only renames.
PULLER_CLUBTYPE = {
    1: "Driver", 2: "3 Wood", 3: "5 Wood", 4: "Hybrid",
    5: "4 Iron", 6: "5 Iron", 7: "6 Iron", 8: "7 Iron",
    9: "8 Iron", 10: "9 Iron", 11: "Pitching Wedge",
    12: "Putter", 14: "Putter",
    36: "Hybrid", 37: "Hybrid",
    42: "54 Wedge", 44: "50 Wedge", 45: "58 Wedge",
    46: "Wedge", 49: "Wedge", 53: "Wedge", 56: "Wedge",
}

# User-friendly display labels for clubTypes the puller doesn't name well.
# Verified by cross-referencing make/model + Smart Distance against the bag.
# IMPORTANT: shots.csv still uses PULLER_CLUBTYPE labels — use both `label`
# (display) and `shots_csv_label` (matching) from paired_bag when joining.
CLUBTYPE_OVERRIDES = {
    35: "3 Hybrid",   # not in puller's map; observed in Qi10 Rescue 19°
}


def _puller_label(ct: int | None) -> str:
    return PULLER_CLUBTYPE.get(ct, f"Club {ct}" if ct is not None else "?")


def _display_label(ct: int | None) -> str:
    if ct is None:
        return "?"
    return CLUBTYPE_OVERRIDES.get(ct) or PULLER_CLUBTYPE.get(ct) or f"Club {ct}"


@dataclass
class ArccosData:
    """Container for everything we load from the Arccos store."""

    rounds: pd.DataFrame
    holes: pd.DataFrame
    shots: pd.DataFrame
    clubs: pd.DataFrame       # puller's clubs.csv — MIXES paired + unpaired
    paired_bag: pd.DataFrame  # authoritative current bag from clubs_v6.json
    handicaps: pd.DataFrame   # per-round drive/approach/chip/sand/putt hcp time series
    courses: pd.DataFrame     # per-course slope/rating/lat-lng from courses/{id}.json
    round_dash: dict          # round_id -> per-round dash detail (SG splits, pace, hole scores)
    store: Path

    def summary(self) -> str:
        return (
            f"Arccos store: {self.store}\n"
            f"  rounds:      {len(self.rounds):>4d}  "
            f"date range {self._date_range(self.rounds)}\n"
            f"  holes:       {len(self.holes):>4d}\n"
            f"  shots:       {len(self.shots):>4d}  "
            f"GPS={'yes' if 'start_lat' in self.shots.columns else 'no'}\n"
            f"  clubs.csv:   {len(self.clubs):>4d}  (paired + unpaired, mixed)\n"
            f"  paired bag:  {len(self.paired_bag):>4d}  "
            f"(authoritative — from clubs_v6.json)\n"
            f"  handicaps:   {len(self.handicaps):>4d}  (per-round shot-type hcp series)\n"
            f"  courses:     {len(self.courses):>4d}  (slope/rating from courses/*.json)\n"
            f"  round_dash:  {len(self.round_dash):>4d}  (per-round SG splits, pace, hole scores)"
        )

    def paired_labels(self) -> set[str]:
        """Set of shots.csv `club` labels for currently-paired clubs.

        Uses `shots_csv_label` (the puller's mapping), not the user-friendly
        `label` — because shots.csv was written with the puller's labels.
        """
        if self.paired_bag.empty or "shots_csv_label" not in self.paired_bag.columns:
            return set()
        return set(self.paired_bag["shots_csv_label"].dropna().tolist())

    def shots_in_bag(self) -> pd.DataFrame:
        """Subset of shots.csv hit with currently-paired clubs only.

        Putts pass through (the GOLO putter has Smart Distance None but is
        paired). For everything else, the shot's `club` label must match a
        paired-bag shots_csv_label.
        """
        labels = self.paired_labels()
        if not labels:
            return self.shots
        s = self.shots
        return s[s["is_putt"].astype(bool) | s["club"].isin(labels)].copy()

    @staticmethod
    def _date_range(df: pd.DataFrame) -> str:
        if df.empty or "date" not in df.columns:
            return "(empty)"
        d = pd.to_datetime(df["date"], errors="coerce").dropna()
        if d.empty:
            return "(no parseable dates)"
        return f"{d.min().date()} to {d.max().date()}"


def _read_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, **kwargs)


def _read_paired_bag(store_path: Path) -> pd.DataFrame:
    """Read clubs_v6.json -> DataFrame of currently-paired clubs.

    Returns empty DataFrame if the raw cache isn't available (e.g. user ran
    the puller without GOLF_STORE pointed at a directory that contains
    `_cache_raw/`).
    """
    src = store_path / "_cache_raw" / "clubs_v6.json"
    if not src.is_file():
        return pd.DataFrame()
    raw = json.loads(src.read_text(encoding="utf-8"))
    paired = (raw.get("clubs") or {}).get("paired") or []
    rows = []
    for c in paired:
        ct = c.get("clubType")
        sd = c.get("smartDistance") or {}
        rows.append({
            "club_id": c.get("clubId"),
            "club_type": ct,
            "label": _display_label(ct),            # user-friendly
            "shots_csv_label": _puller_label(ct),   # matches shots.csv `club`
            "make": c.get("clubMake"),
            "model": c.get("clubModel"),
            "smart_distance_yd": round(sd.get("raw"), 1) if sd.get("raw") else None,
            "longest_yd": round(sd.get("longest"), 1) if sd.get("longest") else None,
            "carry_distance_yd": (round(c.get("carryDistanceMeters") * 1.09361, 1)
                                  if c.get("carryDistanceMeters") else None),
        })
    return pd.DataFrame(rows).sort_values(
        "smart_distance_yd", ascending=False, na_position="last"
    ).reset_index(drop=True)


def _read_handicaps(store_path: Path) -> pd.DataFrame:
    """Read handicaps.json -> per-round handicap-by-shot-type time series."""
    src = store_path / "_cache_raw" / "handicaps.json"
    if not src.is_file():
        return pd.DataFrame()
    raw = json.loads(src.read_text(encoding="utf-8"))
    rows = raw.get("handicaps", [])
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _read_courses(store_path: Path) -> pd.DataFrame:
    """Read courses/*.json -> per-course metadata (slope, rating, location)."""
    src_dir = store_path / "_cache_raw" / "courses"
    if not src_dir.is_dir():
        return pd.DataFrame()
    rows = []
    for path in sorted(src_dir.glob("*.json")):
        try:
            c = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        # Flatten tees: keep the longest tee's slope+rating per course.
        tees = c.get("courseTees") or []
        best_slope, best_rating, best_tee_name = None, None, None
        for t in tees:
            slope = t.get("slope")
            rating = t.get("rating")
            if slope is not None and rating is not None:
                if best_slope is None or (t.get("distance") or 0) > 0:
                    best_slope = slope
                    best_rating = rating
                    best_tee_name = t.get("name")
        rows.append({
            "course_id": c.get("courseId"),
            "name": c.get("name"),
            "city": c.get("city"),
            "state": c.get("state"),
            "lat": c.get("latitude"),
            "lng": c.get("longitude"),
            "mens_par": c.get("mensPar"),
            "no_of_holes": c.get("noOfHoles"),
            "best_tee_name": best_tee_name,
            "slope": best_slope,
            "rating": best_rating,
            "last_played_date": c.get("lastPlayedDate"),
        })
    return pd.DataFrame(rows)


def _read_round_dash(store_path: Path) -> dict:
    """Read rounds/*_dash.json -> {round_id: dash_dict}.

    Each value has sections: overall (with paceOfPlay, holeScores),
    driving, approach, short, putting (with sga, historicSga, accuracy splits).
    """
    src_dir = store_path / "_cache_raw" / "rounds"
    if not src_dir.is_dir():
        return {}
    out = {}
    for path in sorted(src_dir.glob("*_dash.json")):
        try:
            rid = int(path.stem.replace("_dash", ""))
            out[rid] = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return out


def load_arccos(store: str | Path | None = None) -> ArccosData:
    """Load all Arccos artifacts from the data store.

    Args:
        store: directory containing the puller's CSVs and `_cache_raw/`.
               Defaults to ~/golf-data (or $GOLF_STORE if set).

    Raises:
        FileNotFoundError: if the store directory does not exist.
    """
    store_path = Path(store).expanduser() if store else DEFAULT_STORE
    if not store_path.is_dir():
        raise FileNotFoundError(
            f"Arccos store not found at {store_path}. Run "
            "`python ~/tools/golf-reports/setup.py` to create it."
        )

    rounds = _read_csv(store_path / "rounds_summary.csv", parse_dates=["date"])
    holes = _read_csv(store_path / "holes.csv")
    shots = _read_csv(store_path / "shots.csv")
    clubs = _read_csv(store_path / "clubs.csv")
    paired_bag = _read_paired_bag(store_path)
    handicaps = _read_handicaps(store_path)
    courses = _read_courses(store_path)
    round_dash = _read_round_dash(store_path)

    # Numeric coercion on the columns we'll actually analyze. Silent — if
    # Arccos schema changes, we fail open (NaNs) instead of blowing up.
    for col in ("sg_total_arccos", "sg_off_tee_arccos", "sg_approach_arccos",
                "sg_short_arccos", "sg_putting_arccos",
                "sg_total_broadie", "sg_off_tee_broadie", "sg_approach_broadie",
                "sg_short_broadie", "sg_putting_broadie",
                "score", "par", "score_to_par", "putts",
                "gir_pct", "fairway_pct", "avg_drive_yd"):
        if col in rounds.columns:
            rounds[col] = pd.to_numeric(rounds[col], errors="coerce")

    for col in ("shot_distance_yd", "start_dist_to_pin_yd", "end_dist_to_pin_yd",
                "start_lat", "start_lng", "end_lat", "end_lng",
                "sg_shot_approx"):
        if col in shots.columns:
            shots[col] = pd.to_numeric(shots[col], errors="coerce")

    return ArccosData(rounds=rounds, holes=holes, shots=shots, clubs=clubs,
                      paired_bag=paired_bag, handicaps=handicaps,
                      courses=courses, round_dash=round_dash,
                      store=store_path)


if __name__ == "__main__":
    d = load_arccos()
    print(d.summary())
    print()
    if not d.paired_bag.empty:
        print("=== Paired bag (current) ===")
        print(d.paired_bag.to_string(index=False))
