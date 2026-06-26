"""Realistic per-club distance forecast.

Anchors to your MEASURED 7-iron data (74.8 mph club speed, 1.31 smash, 127 yd
avg carry across 125 shots over 5 GC3 sessions) and projects each other club
in the bag using:

  1. Standard amateur-male club-speed progression (delta-mph from 7i),
     since Book1.xlsx's per-club speeds are estimates with unrealistically
     tight (~1 mph) gaps between irons.
  2. Empirical amateur-male carry-per-mph coefficients (from published
     TrackMan/Foresight averages), scaled by an efficiency factor that
     calibrates the 7i row to your measured 127-yd carry — so the model
     is self-consistent at the anchor point.
  3. Target smash factors as a diagnostic reference column (what your
     contact should look like club-by-club; your measured 7i is 1.31
     vs a target of 1.38).

Outputs:
  - realistic_club_distances.csv  — per-club carry + total, current + target
  - Console table for quick reading
"""
from __future__ import annotations

import re

import pandas as pd

# -- Anchor: your measured 7-iron data --------------------------------------
MEASURED_7I_SPEED = 74.8   # mph club speed, 125-shot average
MEASURED_7I_SMASH = 1.31   # actual measured
MEASURED_7I_CARRY = 127.0  # yards, actual measured

# -- Standard amateur-male progression --------------------------------------
# Club-speed delta (mph) above (+) or below (-) measured 7i.
# Based on TrackMan/Foresight published amateur-male progression: ~2.5 mph
# per iron number, larger jumps for hybrids/woods/driver.
DELTA_FROM_7I = {
    "Dr":  +10.0,  # matches Book1.xlsx driver estimate (84 mph)
    "3w":  +7.0,
    "3h":  +6.0,
    "4h":  +4.0,
    "5i":  +5.0,
    "6i":  +3.0,
    "7i":   0.0,
    "8i":  -2.5,
    "9i":  -5.0,
    "PW":  -7.0,
    "GW": -10.0,  # 52°
    "SW": -12.0,  # 56°
    "LW": -14.0,  # 60°
}

# Empirical amateur-male carry-per-mph-of-club-speed (yards per mph).
# These bake in typical launch/spin/contact efficiency for each club type;
# they are NOT the same as ball-speed-based coefficients. Source: TrackMan
# Combine published averages for amateur male, mid-handicap.
CARRY_COEFF = {
    "Dr": 2.47, "3w": 2.24, "3h": 2.05, "4h": 1.95,
    "5i": 1.93, "6i": 1.88, "7i": 1.83, "8i": 1.73, "9i": 1.67,
    "PW": 1.57, "GW": 1.40, "SW": 1.20, "LW": 1.00,
}

# Target smash factor by club — what your contact SHOULD produce with clean
# center-face strike and proper AoA. Your measured 7i smash is 1.31; target
# is 1.38 (a 0.07 gap, which is what's listed in your existing analysis).
TARGET_SMASH = {
    "Dr": 1.47, "3w": 1.43, "3h": 1.41, "4h": 1.40,
    "5i": 1.39, "6i": 1.38, "7i": 1.38, "8i": 1.36, "9i": 1.34,
    "PW": 1.32, "GW": 1.28, "SW": 1.26, "LW": 1.23,
}

# Typical roll factor (carry -> total) by club, firm fairways assumed.
ROLL = {
    "Dr": 1.15, "3w": 1.12, "3h": 1.10, "4h": 1.08,
    "5i": 1.06, "6i": 1.05, "7i": 1.04, "8i": 1.03, "9i": 1.02,
    "PW": 1.02, "GW": 1.01, "SW": 1.01, "LW": 1.00,
}


def main() -> None:
    bag = pd.read_excel("Book1.xlsx")[
        ["Club Abbriation", "Club", "Loft"]
    ].rename(columns={"Club Abbriation": "abbr"})

    bag["loft_deg"] = bag["Loft"].astype(str).apply(
        lambda s: float(re.search(r"(\d+\.?\d*)", s).group(1))
    )
    bag["club_speed_mph"] = bag["abbr"].map(
        lambda a: MEASURED_7I_SPEED + DELTA_FROM_7I.get(a, 0.0)
    )

    # Calibrate efficiency to user's measured 7i carry.
    eff_current = MEASURED_7I_CARRY / (MEASURED_7I_SPEED * CARRY_COEFF["7i"])
    # Target efficiency assumes cleaner strike, optimal launch & spin
    # (your existing GC3 diagnostics already note spin and contact as the
    # priority fixes). A ~6% efficiency gain is the realistic ceiling for an
    # amateur after dialing in launch/spin without raising swing speed.
    eff_target = min(0.99, eff_current * 1.06)

    rows = []
    for _, r in bag.iterrows():
        abbr = r["abbr"]
        if abbr not in CARRY_COEFF:
            continue
        speed = r["club_speed_mph"]
        coeff = CARRY_COEFF[abbr]
        roll = ROLL[abbr]
        smash_tgt = TARGET_SMASH[abbr]

        carry_now = speed * coeff * eff_current
        carry_tgt = speed * coeff * eff_target

        rows.append({
            "Club": f"{abbr} ({r['loft_deg']:g} deg)",
            "Club Speed (mph)": round(speed, 1),
            "Target Smash": f"{smash_tgt:.2f}",
            "Carry now (yd)": round(carry_now),
            "Carry target (yd)": round(carry_tgt),
            "Total now (yd)": round(carry_now * roll),
            "Total target (yd)": round(carry_tgt * roll),
            "Gap to next (yd)": None,  # filled below
        })

    out = pd.DataFrame(rows)

    # Compute carry gap to the NEXT shorter club.
    for i in range(len(out) - 1):
        out.at[i, "Gap to next (yd)"] = int(
            out.iloc[i]["Carry now (yd)"] - out.iloc[i + 1]["Carry now (yd)"]
        )

    print("\n=== REALISTIC PER-CLUB DISTANCES ===")
    print(f"Anchored to measured 7i: {MEASURED_7I_SPEED} mph @ "
          f"{MEASURED_7I_SMASH} smash = {MEASURED_7I_CARRY} yd carry")
    print(f"Efficiency vs amateur-male average: now {eff_current:.2f}, "
          f"target {eff_target:.2f} (with cleaner strike + better launch/spin)\n")
    print(out.to_string(index=False))

    print("\nGap interpretation:")
    print("  8-12 yd  = ideal (clean separation between clubs)")
    print("  <8 yd    = TIGHT (clubs overlap in real conditions)")
    print("  >15 yd   = WIDE (consider gap club)\n")

    out.to_csv("realistic_club_distances.csv", index=False)
    print("Saved: realistic_club_distances.csv")


if __name__ == "__main__":
    main()
