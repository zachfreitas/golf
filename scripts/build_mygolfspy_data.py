"""Parse the MyGolfSpy 2026 iron buyer's-guide tables into clean CSVs.

Each MyGolfSpy guide page has two TablePress tables:
  * a SCORES table (MGS / Accuracy / Distance / Forgiveness score + test year)
  * a ROBOT DATA table (ball speed, carry, total, launch, spin, peak height, descent,
    shot area) -- note MyGolfSpy is the only source here that reports BALL SPEED.

The tables were pulled from the live pages via the DataTables API (all rows across all
pagination) and saved as mgs_*.json in the repo root. Column order differs by page, so we
map columns by header NAME, not position.

Writes:
  data/irons_research/mygolfspy_scores.csv
  data/irons_research/mygolfspy_robot.csv
"""
from __future__ import annotations
import csv
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_SCORES = ROOT / "data" / "irons_research" / "mygolfspy_scores.csv"
OUT_ROBOT = ROOT / "data" / "irons_research" / "mygolfspy_robot.csv"

CATEGORY = {
    "players-distance": "Players Distance",
    "super-game-improvement": "Super Game Improvement",
    "game-improvement": "Game Improvement",
    "players-irons": "Players",
}


def category_from_path(path: str) -> str:
    for key, label in CATEGORY.items():
        if key in path:
            return label
    return "Unknown"


def load(path: str) -> dict:
    raw = open(path, encoding="utf-8").read()
    d = json.loads(raw)
    if isinstance(d, str):      # double-encoded
        d = json.loads(d)
    return d


def hmap(headers: list[str]) -> dict:
    """map normalized header -> index"""
    idx = {}
    for i, h in enumerate(headers):
        idx[re.sub(r"[^a-z]", "", h.lower())] = i
    return idx


def find(idx: dict, *aliases):
    for a in aliases:
        a = re.sub(r"[^a-z]", "", a.lower())
        if a in idx:
            return idx[a]
    return None


def cell(row, i):
    return row[i].strip() if (i is not None and i < len(row)) else ""


def main() -> None:
    scores_rows, robot_rows = [], []
    for f in sorted(glob.glob(str(ROOT / "data" / "irons_research" / "raw" / "mgs_*.json"))):
        d = load(f)
        cat = category_from_path(d["path"])
        for t in d["tables"]:
            idx = hmap(t["headers"])
            is_scores = find(idx, "mgsscore") is not None
            is_robot = find(idx, "ballspd", "ballspeed") is not None
            for r in t["rows"]:
                # OEM & MODEL may be combined or split
                oem_i = find(idx, "oem", "oemmodel")
                model_i = find(idx, "model")
                if find(idx, "oemmodel") is not None and model_i is None:
                    oem, model = "", cell(r, oem_i)      # combined column
                else:
                    oem, model = cell(r, oem_i), cell(r, model_i)
                if is_scores:
                    scores_rows.append({
                        "category": cat, "oem": oem, "model": model,
                        "mgs_score": cell(r, find(idx, "mgsscore")),
                        "accuracy_score": cell(r, find(idx, "accuracyscore")),
                        "distance_score": cell(r, find(idx, "distancescore")),
                        "forgiveness_score": cell(r, find(idx, "forgivenessscore")),
                        "year_tested": cell(r, find(idx, "yeartested", "testingyear")),
                    })
                elif is_robot:
                    robot_rows.append({
                        "category": cat, "oem": oem, "model": model,
                        "ball_spd": cell(r, find(idx, "ballspd", "ballspeed")),
                        "carry": cell(r, find(idx, "carry")),
                        "total": cell(r, find(idx, "total")),
                        "launch": cell(r, find(idx, "launch")),
                        "spin": cell(r, find(idx, "spin")),
                        "peak_ht": cell(r, find(idx, "peakht", "peakheight")),
                        "descent": cell(r, find(idx, "descent")),
                        "shot_area": cell(r, find(idx, "shotarea")),
                    })

    def write(path, rows, fields):
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader(); w.writerows(rows)
        print(f"wrote {len(rows)} -> {path.relative_to(ROOT)}")

    write(OUT_SCORES, scores_rows,
          ["category","oem","model","mgs_score","accuracy_score","distance_score",
           "forgiveness_score","year_tested"])
    write(OUT_ROBOT, robot_rows,
          ["category","oem","model","ball_spd","carry","total","launch","spin",
           "peak_ht","descent","shot_area"])


if __name__ == "__main__":
    main()
