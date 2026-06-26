"""Generate Arccos_Targeted_Diagnostics.ipynb from this Python source.

Run: python build_diagnostics_notebook.py
Output: Arccos_Targeted_Diagnostics.ipynb

Authoring cells in plain Python keeps the analyses diff-friendly and
re-executable via `jupyter nbconvert --execute --inplace`.

Four sections:
  A1. 125-150 yd approach deep-dive (the single biggest SG leak)
  A2. Putt make-% by distance (vs PGA Tour benchmark)
  A3. Lie-penalty matrix (what missing the fairway costs per club)
  C1. Twin Oaks hole-by-hole heat map (your home course)
"""
from __future__ import annotations

import nbformat as nbf


def md(s: str):
    return nbf.v4.new_markdown_cell(s.strip("\n"))


def code(s: str):
    return nbf.v4.new_code_cell(s.strip("\n"))


cells = [
    md(r"""
# Arccos Targeted Diagnostics

Deep-dives on the four highest-stroke-ROI questions surfaced by the broader
Arccos Course Analysis notebook:

1. **125-150 yd approach deep-dive** — the single biggest specific SG leak
   in your game (−0.42 SG/shot × 175+ shots). This section slices by club,
   lie, and wind to find the actual pattern.
2. **Putt make-% by distance** — splits putting (−3.1 SG/round overall) by
   distance band and benchmarks against the PGA Tour. Reveals whether the
   leak is short putts (Aim Point / line) or lag putts (speed control).
3. **Lie-penalty matrix** — what missing the fairway costs per club. Drives
   driver-vs-3W decisions on tight holes with numbers, not vibes.
4. **Twin Oaks hole-by-hole** — your home course (≥30 rounds). Identifies
   nemesis holes that need pre-round mental prep + scoring-opportunity holes
   that you should be more aggressive on.
"""),

    code(r"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from arccos import load_arccos
from arccos import diagnostics as dx

plt.rcParams.update({"figure.figsize": (10, 4), "figure.dpi": 110,
                     "axes.grid": True, "grid.alpha": 0.3})

data = load_arccos()
print(data.summary())
"""),

    md(r"""
## 1. The 125-150 yd approach deep-dive

Slice every approach shot starting in the 125-150 yd band and break it down
by club, lie, and wind. Goal: turn "approach is leaking" into a specific
diagnosis you can attack on the range.
"""),

    code(r"""
res = dx.approach_band_deepdive(data, lo=125, hi=150)
print(f"Total shots in 125-150 yd band: {res['n_total']}")
print(f"Total SG lost in this band: {res['total_sg_lost']:.1f} strokes "
      f"({res['total_sg_lost']/res['n_total']:.2f} per shot avg)")
"""),

    code(r"""
print("--- By CLUB ---")
res["by_club"]
"""),

    code(r"""
print("--- By LIE ---")
res["by_lie"]
"""),

    code(r"""
print("--- By WIND ---")
res["by_wind"]
"""),

    code(r"""
# Visualize the by-club breakdown.
fig, ax = plt.subplots(figsize=(10, 4))
bc = res["by_club"]
colors = ["#d62728" if v < -0.4 else "#ff7f0e" if v < -0.2 else "#2ca02c"
          for v in bc["avg_sg"]]
ax.barh(bc.index.astype(str), bc["avg_sg"], color=colors)
ax.axvline(0, color="black", linewidth=0.5)
ax.set_title(f"125-150 yd approach: per-shot SG by club (n={res['n_total']})")
ax.set_xlabel("Avg SG per shot (negative = losing strokes)")
for i, (n, v) in enumerate(zip(bc["shots"], bc["avg_sg"])):
    ax.text(v - 0.02 if v < 0 else v + 0.02, i, f"n={n}",
            va="center", fontsize=9)
plt.tight_layout(); plt.show()
"""),

    md(r"""
**How to read it.** The shot count next to each bar matters as much as the
SG figure — a brutally negative SG with n=3 might be noise; the same number
with n=50 is a real signal. Cross-reference against the by-lie and by-wind
tables to figure out whether it's the club, the situation, or the user.
"""),

    md(r"""
## 2. Putt make-% by distance

First-putt-only (phantom 0-distance putts filtered out — Arccos logs those
when the ball is already at the hole). Buckets are inclusive of the lower
bound, exclusive of the upper. Tour benchmark from Broadie's published
PGA averages.
"""),

    code(r"""
putts = dx.putt_make_by_distance(data)
putts
"""),

    code(r"""
fig, ax = plt.subplots(figsize=(10, 4.5))
x = np.arange(len(putts))
width = 0.4
ax.bar(x - width/2, putts["make_pct"], width, label="Your make %",
       color="#1f77b4")
ax.bar(x + width/2, putts["tour_pct"], width, label="PGA Tour",
       color="#ff7f0e", alpha=0.7)
ax.set_xticks(x)
ax.set_xticklabels(putts["band"], rotation=20)
ax.set_ylabel("Make %")
ax.set_title("First-putt make-% by distance band — you vs PGA Tour")
ax.legend()
for i, (m, n) in enumerate(zip(putts["make_pct"], putts["attempts"])):
    ax.text(i - width/2, m + 1, f"{m:.0f}% (n={n})", ha="center", fontsize=8)
plt.tight_layout(); plt.show()
"""),

    md(r"""
**Interpretation guide.** Where you're *below* Tour, that's a real practice
opportunity. Where you're *at or above* Tour (often the 18+ ft bands), don't
overinvest — Tour numbers in those bands are surprisingly low because making
a 25-ft putt is mostly luck even for the best players. Long-putt practice
is about avoiding 3-putts (lag distance control), not making them.
"""),

    md(r"""
## 3. Lie-penalty matrix

Smart Distance per club split by lie (tee / fairway / rough / sand) from
`clubs.csv`. **Rough penalty** = fairway distance − rough distance, i.e.
how much carry you lose by missing the fairway. Negative penalty means
you actually got *more* distance from the rough (small samples or hot
rolls — interpret with caution).
"""),

    code(r"""
lies = dx.lie_penalty_matrix(data)
lies
"""),

    code(r"""
# Visualize fairway vs rough for clubs with enough data.
visible = lies[lies["n shots"] >= 8].dropna(subset=["From fairway (yd)", "From rough (yd)"])
fig, ax = plt.subplots(figsize=(10, 5))
y = np.arange(len(visible))
ax.barh(y - 0.2, visible["From fairway (yd)"], 0.4, label="From fairway",
        color="#2ca02c")
ax.barh(y + 0.2, visible["From rough (yd)"], 0.4, label="From rough",
        color="#d62728")
ax.set_yticks(y)
ax.set_yticklabels(visible["display_club"])
ax.set_xlabel("Smart Distance (yd)")
ax.set_title("Fairway vs rough Smart Distance per club")
ax.legend()
for i, (f, r) in enumerate(zip(visible["From fairway (yd)"], visible["From rough (yd)"])):
    pen = f - r
    color = "red" if pen > 5 else "black"
    ax.text(max(f, r) + 3, i, f"penalty: {pen:+.0f} yd",
            va="center", fontsize=9, color=color)
plt.tight_layout(); plt.show()
"""),

    md(r"""
**Decision implication.** When a club's rough penalty is 10+ yards, missing
the fairway with that club is genuinely costly. On tight par-4s where you
can reach the green with a 3-wood from the fairway (penalty 0 yd) vs a
driver from the rough (penalty 10-20 yd), the conservative tee shot may
actually be the longer one to the green.
"""),

    md(r"""
## 4. Twin Oaks hole-by-hole

Per-hole average score-to-par across all rounds at Twin Oaks GC (your most-
played course). `bleed_rank` 1 = worst hole, rank 18 = best. Use this to
target pre-round prep on the holes that hurt most and to be more
aggressive on the ones you score well on.
"""),

    code(r"""
twin = dx.twin_oaks_hole_heatmap(data)
twin
"""),

    code(r"""
fig, ax = plt.subplots(figsize=(11, 4.5))
# Colour: red = bleed, green = score, scaled by par
colors = ["#d62728" if v >= 1.5 else
          "#ff7f0e" if v >= 1.0 else
          "#fdd835" if v >= 0.5 else "#2ca02c"
          for v in twin["avg_to_par"]]
ax.bar(twin.index.astype(str), twin["avg_to_par"], color=colors)
ax.axhline(0, color="black", linewidth=0.5)
ax.set_title("Twin Oaks GC: average score-to-par by hole "
             f"(across {twin['rounds'].max()} rounds)")
ax.set_xlabel("Hole #")
ax.set_ylabel("Strokes over par (avg)")
for i, (par, n, v) in enumerate(zip(twin["par"], twin["rounds"], twin["avg_to_par"])):
    ax.text(i, v + 0.05, f"par {par}\nn={n}", ha="center", fontsize=8)
plt.tight_layout(); plt.show()
"""),

    md(r"""
**Action plan.** Rank-1 holes (your worst) are where pre-round visualization
+ a clear course-management plan moves the needle. Rank-16-to-18 holes are
where you already score well — pin the strategy there, don't get cute.

For the bleed leaders specifically: check the matching by-club and by-lie
patterns from §1 — if hole 1 bleeds and most of your 1st-shot misses end in
rough on a tight fairway, your driver/3W choice is the lever, not your iron.
"""),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python"},
    }
    with open("Arccos_Targeted_Diagnostics.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Wrote Arccos_Targeted_Diagnostics.ipynb")


if __name__ == "__main__":
    main()
