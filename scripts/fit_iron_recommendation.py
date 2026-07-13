"""Iron fit analysis for Zach.

Builds an MPF (Maltby Playability Factor) "preference fingerprint" from Zach's stated
favorite irons + current gamer, then ranks current-market (2023+) irons by how well
they fit that fingerprint. Cross-references his own on-course distance data.

Inputs:
    data/irons_research/maltby_mpf_irons.csv   (built by build_maltby_mpf_dataset.py)
    data/bag_inventory.csv                     (his current bag, incl. real P770 lofts)

Outputs:
    outputs/iron_fit_recommendations.csv       (ranked current irons + fit metrics)
    outputs/iron_fit_shortlist_enriched.csv    (top shortlist + specs enrichment)
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MPF_CSV = ROOT / "data" / "irons_research" / "maltby_mpf_irons.csv"
SPECS_CSV = ROOT / "data" / "irons_research" / "maltby_mpf_brand_specs.csv"
OUT_RANK = ROOT / "outputs" / "iron_fit_recommendations.csv"
OUT_SHORT = ROOT / "outputs" / "iron_fit_shortlist_enriched.csv"

# --------------------------------------------------------------- fit fingerprint
# (brand, model-fragment, year, preference-rank).  Rank 1 = best-ever.
FAVORITES = [
    ("CALLAWAY", "X-20 Tour", 2007, 1),   # #1 all-time favorite
    ("TAYLORMADE", "P770", 2023, 2),      # #2 + current gamer; loved for consistency
    ("CALLAWAY", "X-22 Tour", 2009, 3),   # #3; also loved for consistency
]
# Preference-weighted target MPF (weights 3:2:1 by rank).
FAV_MPF = {1: 716, 2: 567, 3: 594}
TARGET = round((FAV_MPF[1] * 3 + FAV_MPF[2] * 2 + FAV_MPF[3] * 1) / 6)  # ~646
GAMER_MPF = FAV_MPF[2]      # 567  (P770 2023)
BEST_MPF = FAV_MPF[1]       # 716  (X-20 Tour) -- his proven "best" forgiveness level

# Preferred band: from gamer up to best-ever, with headroom toward more forgiveness
# (justified by L1 skill data: dispersion + 125-150yd worst zone + zone-reg 33% ceiling).
BAND_LO, BAND_HI = 590, 740

# ---------------------------------------------------- editorial notes (commentary)
# Loft / MOI / CG / head-weight now come from the GolfWorks per-brand engineering PDFs
# (data/irons_research/maltby_mpf_brand_specs.csv) -- authoritative measured specs, not
# hand-entry. These NOTES only add human commentary on construction/consistency.
NOTES = {
    ("TAYLORMADE", "P790"): dict(construction="Hollow forged + SpeedFoam Air + tungsten",
        family="Players Distance", consistency="Excellent",
        note="Same TM family as gamer; benchmark players-distance iron"),
    ("TITLEIST", "T200"): dict(construction="Forged L-face + high-density tungsten",
        family="Players Distance", consistency="Excellent", note="Very tight dispersion"),
    ("TITLEIST", "T250"): dict(construction="Forged face + tungsten",
        family="Players Distance", consistency="Excellent", note="2025 T200 successor"),
    ("MIZUNO", "JPX 925 Hot Metal Pro"): dict(construction="One-piece Chromoly 4335",
        family="Players Distance", consistency="Excellent", note="Renowned feel/consistency"),
    ("MIZUNO", "JPX Hot Metal Pro"): dict(construction="One-piece Chromoly",
        family="Players Distance", consistency="Excellent", note="Clean 'Pro' profile"),
    ("MIZUNO", "JPX 923 Forged"): dict(construction="Grain-flow forged HD Chromoly",
        family="Players Distance (forged)", consistency="Very good", note="Softest feel"),
    ("COBRA", "Aerojet"): dict(construction="Hollow split, PWR-Bridge, tungsten",
        family="Players Distance", consistency="Very good", note="High forgiveness/value"),
    ("COBRA", "Dark Speed"): dict(construction="Hollow, PWR-Bridge, tungsten",
        family="Players Distance", consistency="Very good", note="Aerojet successor"),
    ("PXG", "0311 P"): dict(construction="Hollow forged, XCOR2 core",
        family="Players Distance", consistency="Very good", note="Fully custom-fit brand"),
    ("TAYLORMADE", "P790 Forged"): dict(construction="Fully forged players distance",
        family="Players Distance", consistency="Excellent", note="Forged P790 variant"),
    ("TAYLORMADE", "P770"): dict(construction="Compact hollow forged + SpeedFoam Air",
        family="Players Distance (compact)", consistency="Excellent", note="Gamer's newer sibling"),
    ("TITLEIST", "T150"): dict(construction="Forged face + tungsten (strong-loft players)",
        family="Players / Players Distance", consistency="Very good", note="Compact, low offset"),
}


def load_mpf() -> pd.DataFrame:
    df = pd.read_csv(MPF_CSV)
    df = df[df["iron_number"].astype(str) == "6"]  # #6 is the chart's reference head
    return df


def load_specs() -> pd.DataFrame:
    """Real per-model engineering specs from the GolfWorks per-brand PDFs."""
    s = pd.read_csv(SPECS_CSV)
    for c in ("year", "mpf", "loft", "moi", "vcog", "head_weight_g"):
        s[c] = pd.to_numeric(s[c], errors="coerce")
    # Join key = (brand, year, mpf): mpf+year is ~unique and matches across documents.
    s = s.dropna(subset=["mpf"]).drop_duplicates(subset=["brand", "year", "mpf"])
    return s[["brand", "year", "mpf", "loft", "moi", "vcog", "head_weight_g"]]


def fit_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["vs_P770_gamer"] = df["mpf"] - GAMER_MPF
    df["vs_X20Tour_best"] = df["mpf"] - BEST_MPF
    df["in_pref_band"] = df["mpf"].between(BAND_LO, BAND_HI)
    # Fit score: closeness to a forgiveness target that leans toward his best-ever
    # iron (700), rewarding the whole preferred band. 100 = bullseye.
    aim = 700
    df["fit_score"] = (100 - (df["mpf"] - aim).abs() / 2.0).clip(lower=0).round(1)
    return df


def tier(mpf: int) -> str:
    if 680 <= mpf <= 740:
        return "A - recreate the X-20 Tour (max forgiveness, players look)"
    if 620 <= mpf < 680:
        return "B - P770 replacement, slight forgiveness bump"
    if 740 < mpf <= 820:
        return "C - more forgiving than he's ever gamed (super game-improvement)"
    return "D - outside preferred range"


def notes_for(brand: str, model: str) -> dict:
    best = {}
    for (b, frag), spec in NOTES.items():
        if brand == b and frag.lower() in model.lower():
            if len(frag) > len(best.get("_frag", "")):  # prefer most specific match
                best = {**spec, "_frag": frag}
    best.pop("_frag", None)
    return best


# Reference MOI of Zach's fingerprint clubs (from brand-spec PDFs), for context.
REF_MOI = {"X-20 Tour (best)": 13.71, "P770 (gamer)": 11.54, "X-22 Tour": 12.57}


def main() -> None:
    df = load_mpf()
    specs = load_specs()
    cur = df[df["year"] >= 2023].copy()
    cur = fit_metrics(cur)
    cur["tier"] = cur["mpf"].apply(tier)

    # Merge REAL engineering specs (loft/MOI/CG/weight) on (brand, year, mpf).
    cur = cur.merge(specs, on=["brand", "year", "mpf"], how="left")
    cur = cur.sort_values(["fit_score", "year", "mpf"], ascending=[False, False, False])

    cols = ["brand", "model", "year", "mpf", "category", "tier",
            "vs_P770_gamer", "vs_X20Tour_best", "fit_score", "in_pref_band",
            "loft", "moi", "vcog", "head_weight_g"]
    cur[cols].to_csv(OUT_RANK, index=False)
    print(f"wrote {len(cur)} current irons -> {OUT_RANK.relative_to(ROOT)}")

    # Shortlist = current irons in tiers A/B, with real specs + editorial notes.
    short = cur[cur["tier"].str.startswith(("A", "B"))].copy()
    recs = []
    for _, r in short.iterrows():
        e = notes_for(r["brand"], r["model"])
        recs.append({
            "brand": r["brand"], "model": r["model"], "year": int(r["year"]),
            "mpf": int(r["mpf"]), "tier": r["tier"][0], "fit_score": r["fit_score"],
            "loft_6i": r["loft"], "moi": r["moi"], "vcog_cg": r["vcog"],
            "head_weight_g": r["head_weight_g"],
            "vs_gamer_moi": (round(r["moi"] - REF_MOI["P770 (gamer)"], 2)
                             if pd.notna(r["moi"]) else ""),
            "construction": e.get("construction", ""), "family": e.get("family", ""),
            "consistency": e.get("consistency", ""), "note": e.get("note", ""),
        })
    short_df = pd.DataFrame(recs).sort_values(["fit_score", "year"], ascending=[False, False])
    short_df.to_csv(OUT_SHORT, index=False)
    print(f"wrote {len(short_df)} shortlist irons -> {OUT_SHORT.relative_to(ROOT)}")

    # Console summary
    print(f"\nFINGERPRINT (MPF | MOI): "
          f"X-20 Tour best={BEST_MPF}|{REF_MOI['X-20 Tour (best)']}  "
          f"P770 gamer={GAMER_MPF}|{REF_MOI['P770 (gamer)']}  "
          f"X-22 Tour=594|{REF_MOI['X-22 Tour']}  | band {BAND_LO}-{BAND_HI}")
    print("\n=== TOP 15 CURRENT IRONS BY FIT ===")
    show = cur.head(15)[["brand", "model", "year", "mpf", "loft", "moi",
                         "vs_P770_gamer", "fit_score"]]
    with pd.option_context("display.max_colwidth", 40, "display.width", 160):
        print(show.to_string(index=False))


if __name__ == "__main__":
    main()
