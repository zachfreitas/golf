"""Load Arccos on-course CSVs produced by chrisdecali/golf-reports.

Default store: ~/golf-data/ (set by setup.py / GOLF_STORE env var).
Override via load_arccos(store=...).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DEFAULT_STORE = Path(os.environ.get("GOLF_STORE") or "~/golf-data").expanduser()


@dataclass
class ArccosData:
    """Container for the four core Arccos artifacts.

    Any DataFrame may be empty if the corresponding CSV wasn't produced
    (e.g. clubs.csv requires enough rounds for per-club aggregates).
    """

    rounds: pd.DataFrame      # one row per round
    holes: pd.DataFrame       # one row per hole-round
    shots: pd.DataFrame       # one row per shot (GPS only if --include-gps)
    clubs: pd.DataFrame       # per-club aggregates
    store: Path               # where these were loaded from

    def summary(self) -> str:
        return (
            f"Arccos store: {self.store}\n"
            f"  rounds: {len(self.rounds):>4d}  "
            f"date range {self._date_range(self.rounds)}\n"
            f"  holes:  {len(self.holes):>4d}\n"
            f"  shots:  {len(self.shots):>4d}  "
            f"GPS={'yes' if 'start_lat' in self.shots.columns else 'no'}\n"
            f"  clubs:  {len(self.clubs):>4d}"
        )

    @staticmethod
    def _date_range(df: pd.DataFrame) -> str:
        if df.empty or "date" not in df.columns:
            return "(empty)"
        d = pd.to_datetime(df["date"], errors="coerce").dropna()
        if d.empty:
            return "(no parseable dates)"
        return f"{d.min().date()} to {d.max().date()}"


def _read_csv(path: Path, **kwargs) -> pd.DataFrame:
    """Read a CSV if it exists, returning an empty DataFrame otherwise."""
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, **kwargs)


def load_arccos(store: str | Path | None = None) -> ArccosData:
    """Load all four core Arccos CSVs from the data store.

    Args:
        store: directory containing the CSVs. Defaults to ~/golf-data
               (or $GOLF_STORE if set).

    Returns:
        ArccosData with rounds / holes / shots / clubs DataFrames.

    Raises:
        FileNotFoundError: if the store directory does not exist.
    """
    store_path = Path(store).expanduser() if store else DEFAULT_STORE
    if not store_path.is_dir():
        raise FileNotFoundError(
            f"Arccos store not found at {store_path}. Run "
            "`python /c/Users/zfreitas/tools/golf-reports/setup.py` to create it."
        )

    rounds = _read_csv(store_path / "rounds_summary.csv", parse_dates=["date"])
    holes = _read_csv(store_path / "holes.csv")
    shots = _read_csv(store_path / "shots.csv")
    clubs = _read_csv(store_path / "clubs.csv")

    # Best-effort numeric coercion on the columns we'll analyze. Keep silent —
    # if Arccos schema changes, this fails open (NaNs) rather than blowing up.
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
                      store=store_path)


if __name__ == "__main__":
    print(load_arccos().summary())
