"""Cool Clubs robotic iron data (2026), transcribed from their .webp data cards.

Test conditions (constant across Cool Clubs iron cards): 7-iron | 80 mph club speed |
-2 deg AoA | 0 deg face/path | 0.5" off-center | Titleist Pro V1 RCT | KBS Tour 110g steel.
Note this differs from Golf Digest (82 mph, and GD used the models' own stock shafts), so
absolute numbers are NOT directly comparable across the two sources -- compare within a
source. Values transcribed from the images by vision extraction.

Only the "Key Data" cards carry full trajectory numbers (loft/launch/spin/peak/carry/
descent). The graph-only cards (Cobra, Mizuno, and the Ping/Wilson graphs) provide 95%
shot-area totals (yds^2) but no trajectory; those totals are captured in `disp_area_yds2`.

Writes data/irons_research/coolclubs_iron_data.csv
"""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "irons_research" / "coolclubs_iron_data.csv"

# brand, model, loft, launch, spin, peak_ft, carry, descent, disp_area_yds2, note
ROWS = [
    # ---- Ping (Key Data card) ----
    ("PING", "G730", 28, 20.0, 4310, 91, 170, 46, 155, ""),
    ("PING", "i530", 29, 20.0, 4506, 91, 168, 46, 107, ""),
    ("PING", "G740", 28, 20.9, 4787, 92, 162, 47, 82, ""),
    ("PING", "i540", 29, 20.8, 4767, 91, 161, 46, 72, ""),
    # ---- Wilson Staff Model (Key Data card) ----
    ("WILSON", "Staff MB", 34, 23.0, 5908, 95, 151, 49, 72, ""),
    ("WILSON", "Staff CB", 34, 23.0, 6007, 96, 149, 49, 56, ""),
    ("WILSON", "Staff XB", 32, 21.7, 5467, 93, 156, 48, 85, ""),
    # ---- Wilson DynaPWR Forged (Key Data card) ----
    ("WILSON", "DynaPWR Forged (2024)", 30.5, 20.2, 5277, 91, 161, 47, 100, "old"),
    ("WILSON", "DynaPWR Forged (2026)", 30.5, 21.0, 4902, 94, 163, 47, 117, "new"),
    # ---- Callaway Quantum (Key Data card) ----
    ("CALLAWAY", "Quantum Max", 29, 20.4, 4458, 91, 166, 46, 74, ""),
    ("CALLAWAY", "Quantum Max OS", 29, 20.4, 4195, 91, 168, 46, 99, ""),
    ("CALLAWAY", "Quantum Max Fast", 28, 19.4, 4453, 88, 168, 45, 74, ""),
    # ---- Graph-only cards: dispersion 95% area only (no trajectory) ----
    ("COBRA", "3DP Tour", "", "", "", "", "", "", 74, "dispersion-only card"),
    ("COBRA", "3DP X", "", "", "", "", "", "", 92, "dispersion-only card"),
    ("COBRA", "3DP MB", "", "", "", "", "", "", 96, "dispersion-only card"),
    ("MIZUNO", "Pro M-13", "", "", "", "", "", "", 93, "dispersion-only card"),
    ("MIZUNO", "Pro M-15", "", "", "", "", "", "", 57, "dispersion-only card"),
    ("MIZUNO", "Pro 243", "", "", "", "", "", "", 115, "dispersion-only card"),
    ("MIZUNO", "Pro 245", "", "", "", "", "", "", 81, "dispersion-only card"),
]

FIELDS = ["brand", "model", "iron_tested", "loft_deg", "launch_deg", "spin_rpm",
          "peak_ft", "carry_yds", "descent_deg", "disp_area_yds2", "note",
          "club_speed_mph", "aoa_deg", "ball", "shaft", "source"]


def main() -> None:
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        for b, m, loft, la, spin, peak, carry, desc, disp, note in ROWS:
            w.writerow([b, m, "7-iron", loft, la, spin, peak, carry, desc, disp, note,
                        80, -2, "Titleist Pro V1 RCT", "KBS Tour 110g", "Cool Clubs"])
    print(f"wrote {len(ROWS)} Cool Clubs rows -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
