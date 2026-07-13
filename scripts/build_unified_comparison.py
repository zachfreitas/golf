"""Unified cross-source iron comparison for Zach's shortlist.

Joins every source into ONE row per candidate iron:
  * Maltby per-brand specs  -> loft, MOI, adjusted VCOG (the design levers)
  * Golf Digest robot (82mph)-> spin, descent, peak, dispersion (his launch deficit)
  * Cool Clubs robot (80mph) -> launch, spin, peak, descent
  * MyGolfSpy robot          -> ball speed, carry, spin, descent
  * MyGolfSpy scores         -> independent MGS / Accuracy / Distance / Forgiveness

Everything is normalized to his gamer (TaylorMade P770 2023) and ranked for his ACTUAL
need: more spin + steeper descent + higher launch (green-holding), while staying forgiving.

His P770 baseline row uses his own GC3 7-iron numbers (~75 mph) -- flagged, since the robot
sources swing faster, so his absolute spin isn't directly comparable to the 80-82 mph rows.

Output: outputs/iron_unified_comparison.csv
"""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "irons_research"
OUT = ROOT / "outputs" / "iron_unified_comparison.csv"

BASE = dict(adj_vcog=-0.044, moi=11.54, loft=29.0)  # his P770 (2023), 6-iron ref

# Shortlist: display name, brand, model match tokens (ALL must appear, alnum-only).
SHORTLIST = [
    ("Ping i240",                    "PING",       ["i240"]),
    ("TaylorMade Qi4D Max HL",       "TAYLORMADE", ["qi4d", "hl"]),
    ("Ping G740",                    "PING",       ["g740"]),
    ("Wilson Staff Dynapwr",         "WILSON",     ["dynapwr"]),
    ("Mizuno Pro M-13",              "MIZUNO",     ["m13"]),
    ("Mizuno Pro M-15",              "MIZUNO",     ["m15"]),
    ("Titleist T250",                "TITLEIST",   ["t250"]),
    ("Callaway Apex Ti Fusion",      "CALLAWAY",   ["tifusion"]),
    ("TaylorMade P790",              "TAYLORMADE", ["p790"]),
    ("Ping i540",                    "PING",       ["i540"]),
    ("PXG 0311P",                    "PXG",        ["0311p"]),
]


def na(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def match(df, brand_col, model_col, brand, tokens, prefer_year=True, year_col=None):
    sub = df[df[brand_col].map(na) == na(brand)]
    hits = []
    for _, r in sub.iterrows():
        m = na(r[model_col])
        if all(tok in m for tok in tokens):
            hits.append(r)
    if not hits:
        return None
    if prefer_year and year_col:
        hits.sort(key=lambda r: -(pd.to_numeric(r.get(year_col), errors="coerce") or 0))
    return hits[0]


def main() -> None:
    specs = pd.read_csv(D / "maltby_mpf_brand_specs.csv")
    for c in ("loft", "moi", "adj_vcog", "year", "mpf"):
        specs[c] = pd.to_numeric(specs[c], errors="coerce")
    gd = pd.read_csv(D / "golfdigest_robot_2026.csv")
    cc = pd.read_csv(D / "coolclubs_iron_data.csv")
    mr = pd.read_csv(D / "mygolfspy_robot.csv")
    ms = pd.read_csv(D / "mygolfspy_scores.csv")

    rows = []
    for name, brand, tokens in SHORTLIST:
        sp = match(specs, "brand", "model", brand, tokens, True, "year")
        g = match(gd, "brand", "model", brand, tokens)
        c = match(cc, "brand", "model", brand, tokens)
        m = match(mr, "oem", "model", brand, tokens)
        s = match(ms, "oem", "model", brand, tokens)
        rows.append({
            "iron": name,
            # Maltby design levers
            "loft6i": sp.loft if sp is not None else "",
            "MOI": sp.moi if sp is not None else "",
            "adjVCOG": sp.adj_vcog if sp is not None else "",
            "MPF": sp.mpf if sp is not None else "",
            # Golf Digest robot (82mph)
            "GD_spin": g.spin_rpm if g is not None else "",
            "GD_descent": g.descent_deg if g is not None else "",
            "GD_peak_ft": g.peak_ft if g is not None else "",
            "GD_disp_sqft": g.dispersion_sqft95 if g is not None else "",
            # Cool Clubs robot (80mph steel)
            "CC_spin": c.spin_rpm if c is not None else "",
            "CC_launch": c.launch_deg if c is not None else "",
            "CC_descent": c.descent_deg if c is not None else "",
            # MyGolfSpy robot
            "MGS_ballspd": m.ball_spd if m is not None else "",
            "MGS_carry": m.carry if m is not None else "",
            "MGS_spin": m.spin if m is not None else "",
            "MGS_descent": m.descent if m is not None else "",
            # MyGolfSpy scores
            "MGS_score": s.mgs_score if s is not None else "",
            "MGS_forgive": s.forgiveness_score if s is not None else "",
        })
    df = pd.DataFrame(rows)

    # Normalize design levers to his P770.
    df["dMOI_vsP770"] = pd.to_numeric(df.MOI, errors="coerce") - BASE["moi"]
    df["dAdjVCOG_vsP770"] = pd.to_numeric(df.adjVCOG, errors="coerce") - BASE["adj_vcog"]
    df["dLoft_vsP770"] = pd.to_numeric(df.loft6i, errors="coerce") - BASE["loft"]

    # Launch-fit for HIS deficit: reward GD spin + descent + peak (green-holding),
    # plus a forgiveness nudge (MOI). Higher = better for Zach.
    def z(col):
        v = pd.to_numeric(df[col], errors="coerce")
        return (v - v.mean()) / v.std(ddof=0)
    df["launch_fit"] = (z("GD_spin") + z("GD_descent") + z("GD_peak_ft")
                        + 0.5 * z("MOI").fillna(0)).round(2)

    # Inject his P770 GC3 baseline for reference (his swing ~75mph, not robot).
    base_row = {c: "" for c in df.columns}
    base_row.update({"iron": ">> YOUR P770 (GC3 @75mph, not robot)",
                     "loft6i": 29, "MOI": 11.54, "adjVCOG": -0.044,
                     "GD_spin": "4949*", "GD_descent": "39.5*", "GD_peak_ft": "61*",
                     "launch_fit": ""})

    df = df.sort_values("launch_fit", ascending=False)
    df = pd.concat([df, pd.DataFrame([base_row])], ignore_index=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}\n")

    view = ["iron","loft6i","MOI","adjVCOG","GD_spin","GD_descent","GD_peak_ft",
            "MGS_ballspd","MGS_forgive","dMOI_vsP770","dAdjVCOG_vsP770","launch_fit"]
    with pd.option_context("display.width", 220, "display.max_colwidth", 30):
        print(df[view].to_string(index=False))
    print("\n* = your GC3 numbers at ~75 mph (robot rows are 80-82 mph); compare rankings, not absolutes.")
    print("Lower adjVCOG = launches higher for its loft; higher MOI = more forgiving;")
    print("higher GD_spin/descent/peak = better green-holding (your deficit).")


if __name__ == "__main__":
    main()
