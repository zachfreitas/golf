"""Capstone iron synthesis for Zach's ACTUAL problem.

His GC3 data shows the issue isn't strike or distance -- it's low spin, low peak height,
and shallow descent (his irons won't hold greens). So the right question is NOT "which
iron is most forgiving" but "which iron gives me more spin / height / descent (green-
holding) while staying forgiving and consistent, without jacked lofts that kill spin".

This joins:
  * Golf Digest 2026 robot data (7-iron @ 82 mph): spin, dynamic loft, descent, peak -> the
    launch behaviour he lacks (data/irons_research/golfdigest_robot_2026.csv)
  * Maltby per-brand specs: loft, MOI, adjusted VCOG (loft-normalized CG) -> the design
    levers (data/irons_research/maltby_mpf_brand_specs.csv)

Baseline for normalization = his gamer TaylorMade P770 2023 (adj_vcog -0.044, MOI 11.54).

Output: outputs/iron_fit_for_launch.csv (ranked for his green-holding need + normalized cols)
"""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ROBOT = ROOT / "data" / "irons_research" / "golfdigest_robot_2026.csv"
SPECS = ROOT / "data" / "irons_research" / "maltby_mpf_brand_specs.csv"
OUT = ROOT / "outputs" / "iron_fit_for_launch.csv"

# His P770 (2023) baseline. vcog_eff = Basic VCOG + Adjusted VCOG (0.788 + -0.044).
BASE_VCOGEFF, BASE_MOI, BASE_LOFT = 0.744, 11.54, 29.0


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def load_specs() -> pd.DataFrame:
    s = pd.read_csv(SPECS)
    for c in ("loft", "moi", "vcog", "adj_vcog", "vcog_eff", "rcog", "year", "mpf"):
        s[c] = pd.to_numeric(s[c], errors="coerce")
    s = s[s.year >= 2025]
    return s


def best_spec(brand: str, model: str, specs: pd.DataFrame):
    """Token-overlap match of a robot model to a Maltby spec row (same brand)."""
    bn = norm(brand)
    cand = specs[specs.brand.map(norm) == bn]
    if cand.empty:
        return None
    mtok = set(re.findall(r"[a-z0-9]+", model.lower()))
    best, best_score = None, 0
    for _, row in cand.iterrows():
        stok = set(re.findall(r"[a-z0-9]+", str(row.model).lower())) - {"6", "iron", "6"}
        overlap = len(mtok & stok)
        # require a meaningful shared token (model name/number), not just brand
        score = overlap + (0.1 if abs((row.loft or 99) - 0) < 99 else 0)
        if overlap >= 1 and score > best_score:
            best, best_score = row, score
    return best


def main() -> None:
    robot = pd.read_csv(ROBOT)
    specs = load_specs()

    recs = []
    for _, r in robot.iterrows():
        sp = best_spec(r.brand, r.model, specs)
        rec = {
            "category": r.category, "brand": r.brand, "model": r.model,
            "iron_tested": r.iron_tested,
            "spin_rpm": r.spin_rpm, "dyn_loft_deg": r.dyn_loft_deg,
            "descent_deg": r.descent_deg, "peak_ft": r.peak_ft,
            "carry_yds": r.carry_yds, "dispersion_sqft95": r.dispersion_sqft95,
            "loft_6i": (sp.loft if sp is not None else ""),
            "vcog_eff": (sp.vcog_eff if sp is not None else ""),
            "moi": (sp.moi if sp is not None else ""),
        }
        recs.append(rec)
    df = pd.DataFrame(recs)

    # Green-holding score for HIS deficit: he needs MORE spin, steeper descent, higher peak.
    def z(col):
        v = pd.to_numeric(df[col], errors="coerce")
        return (v - v.mean()) / v.std(ddof=0)
    df["green_hold_z"] = (z("spin_rpm") + z("descent_deg") + z("peak_ft")).round(2)
    # Forgiveness (where MOI known), normalized vs his P770.
    df["moi_vs_P770"] = pd.to_numeric(df["moi"], errors="coerce") - BASE_MOI
    df["effvcog_vs_P770"] = (pd.to_numeric(df["vcog_eff"], errors="coerce") - BASE_VCOGEFF).round(3)
    df["loft_vs_P770"] = pd.to_numeric(df["loft_6i"], errors="coerce") - BASE_LOFT

    # Combined fit: primarily green-holding, plus a forgiveness nudge where MOI is known.
    moi_z = z("moi").fillna(0)
    df["launch_fit"] = (df["green_hold_z"] + 0.5 * moi_z).round(2)

    df = df.sort_values("launch_fit", ascending=False)
    cols = ["category","brand","model","iron_tested","spin_rpm","descent_deg","peak_ft",
            "carry_yds","loft_6i","vcog_eff","moi","moi_vs_P770","effvcog_vs_P770",
            "loft_vs_P770","green_hold_z","launch_fit"]
    df[cols].to_csv(OUT, index=False)
    print(f"wrote {len(df)} -> {OUT.relative_to(ROOT)}\n")
    print("Ranked for Zach's need (more spin/height/descent + forgiveness):")
    show = df.head(14)[["brand","model","category","spin_rpm","descent_deg","peak_ft",
                        "moi","loft_6i","launch_fit"]]
    with pd.option_context("display.width",170,"display.max_colwidth",22):
        print(show.to_string(index=False))
    print(f"\nHis P770 baseline: effVCOG {BASE_VCOGEFF}, MOI {BASE_MOI}, 6i loft {BASE_LOFT}")
    print("His GC3 7i: spin ~4950 @75mph, descent 39.5deg, peak 61ft  (all below target)")


if __name__ == "__main__":
    main()
