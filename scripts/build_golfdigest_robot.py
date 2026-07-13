"""Golf Digest 2026 robotic iron-test data (Golf Laboratories).

Transcribed from the three Golf Digest 2026 robot-test articles (game-improvement,
players, players-distance). All figures are for the 7-IRON of each model under identical
robot delivery: ~82 mph club speed, -3 deg AoA, Titleist Pro V1, 36 shots per head.
Source: Golf Laboratories Robotic Testing (dates per category below).

Writes data/irons_research/golfdigest_robot_2026.csv
Peak height is reported by GD with an inch mark but the values are feet (kept as-is here).
"""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "irons_research" / "golfdigest_robot_2026.csv"

# category, brand, model, spin_rpm, dyn_loft, spin_axis, carry_yds, descent_deg, peak_ft, disp_sqft95, test_date
ROWS = [
    # ---- Players Distance (7i, 82mph, -3 AoA, Mar 2026) ----
    ("Players Distance","PING","i540",4429,22.2,"-4.5 DRAW",160.0,42.8,81,148,"Mar 2026"),
    ("Players Distance","TAYLORMADE","P790",4911,24.0,"-1.8 DRAW",157.9,44.5,84,168,"Mar 2026"),
    ("Players Distance","PXG","0311P Gen 8",4919,24.5,"-1.8 DRAW",161.5,45.4,89,167,"Mar 2026"),
    ("Players Distance","MIZUNO","Pro M-15",5113,24.0,"+0.2 FADE",153.5,43.4,80,337,"Mar 2026"),
    ("Players Distance","CALLAWAY","Apex Ai200",5193,24.9,"-3.3 DRAW",152.5,44.9,82,180,"Mar 2026"),
    ("Players Distance","WILSON","Staff Model XB",5487,25.9,"-2.5 DRAW",149.5,45.3,84,299,"Mar 2026"),
    ("Players Distance","CALLAWAY","Apex Ti Fusion",5557,26.1,"-1.5 DRAW",151.3,45.6,86,227,"Mar 2026"),
    # ---- Game Improvement (7i, 82mph, Jul 2026) -- dispersion from robot agent ----
    ("Game Improvement","PXG","0311XP Gen 8",4420,22.2,"+1.2 FADE",164.2,42.7,81,361,"Jul 2026"),
    ("Game Improvement","PING","G740",4999,23.5,"-0.2 DRAW",158.8,44.7,86,261,"Jul 2026"),
    ("Game Improvement","COBRA","3DP King",5034,23.5,"-2.3 DRAW",156.5,42.6,78,167,"Jul 2026"),
    ("Game Improvement","CALLAWAY","Apex Forged",5130,25.4,"+2.6 FADE",157.4,45.1,84,232,"Jul 2026"),
    ("Game Improvement","CALLAWAY","Apex Ti",5144,25.4,"-1.2 DRAW",155.3,45.0,86,215,"Jul 2026"),
    ("Game Improvement","TAYLORMADE","Qi4D Max",5255,24.6,"-0.6 DRAW",152.2,44.0,80,178,"Jul 2026"),
    ("Game Improvement","COBRA","3DPx",5387,24.9,"-0.5 DRAW",153.0,44.5,82,277,"Jul 2026"),
    ("Game Improvement","WILSON","Staff Dynapwr",5604,25.9,"+1.3 FADE",152.7,45.8,88,169,"Jul 2026"),
    ("Game Improvement","TAYLORMADE","Qi4D Max HL",5843,26.9,"-2.2 DRAW",147.0,45.9,84,181,"Jul 2026"),
    # ---- Players (7i, 82mph, Jun 2026) -- dispersion from article ----
    ("Players","PXG","0311T Gen8",5244,25.4,"-1.9 DRAW",155.8,45.5,88,326,"Jun 2026"),
    ("Players","CALLAWAY","Apex Ai 150",5289,26.5,"-1.0 DRAW",149.5,46.2,86,303,"Jun 2026"),
    ("Players","COBRA","3DP Tour",5513,25.3,"+0.5 FADE",150.7,44.7,83,227,"Jun 2026"),
    ("Players","PING","i240",5662,26.8,"-2.5 DRAW",146.8,45.6,85,137,"Jun 2026"),
    ("Players","MIZUNO","Pro M-13",5799,26.4,"-2.4 DRAW",148.8,45.7,85,165,"Jun 2026"),
    ("Players","WILSON","Staff Model",5903,26.6,"-2.8 DRAW",144.5,45.5,81,372,"Jun 2026"),
    ("Players","COBRA","3DP MB",5927,26.9,"-2.6 DRAW",147.1,45.5,84,246,"Jun 2026"),
    ("Players","MIZUNO","Pro S-1",6113,28.0,"-1.6 DRAW",146.5,46.8,87,223,"Jun 2026"),
    ("Players","CALLAWAY","X Forged",6165,27.3,"-2.4 DRAW",143.5,46.2,84,279,"Jun 2026"),
    ("Players","WILSON","Staff Model CB",6476,29.3,"+0.5 FADE",136.6,46.8,83,310,"Jun 2026"),
]

FIELDS = ["category","brand","model","iron_tested","spin_rpm","dyn_loft_deg","spin_axis",
          "carry_yds","descent_deg","peak_ft","dispersion_sqft95","robot_club_speed_mph",
          "ball","shots","source","test_date"]

def main():
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(FIELDS)
        for cat,brand,model,spin,dl,axis,carry,desc,peak,disp,date in ROWS:
            w.writerow([cat,brand,model,"7-iron",spin,dl,axis,carry,desc,peak,
                        "" if disp is None else disp,82,"Titleist Pro V1",36,
                        "Golf Laboratories (Golf Digest)",date])
    print(f"wrote {len(ROWS)} robot rows -> {OUT.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
