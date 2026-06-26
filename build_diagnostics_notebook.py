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

Per-hole performance at Twin Oaks GC (your most-played course). Three
ranks help distinguish different kinds of "bad hole":

- **`avg_rank`** — sorted by mean strokes-over-par. Highlights holes where
  blow-ups (triples, others) inflate the average.
- **`double_rank`** — sorted by % of rounds you make double-bogey-or-worse.
  Highlights holes where the *typical* outcome is bad, not just the worst
  outcome. This often matches "feel" better than the average.
- **`nemesis_rank`** — composite of the two. Lower = worse hole overall.

A hole with `avg_rank=1` but `double_rank=10` blows up occasionally but
plays normally most rounds. A hole with `double_rank=1` but `avg_rank=5`
beats you down day after day even if it rarely cataclysmically explodes.
"""),

    code(r"""
twin = dx.twin_oaks_hole_heatmap(data)
twin
"""),

    code(r"""
# Two-panel view: avg-to-par on top, double-bogey-or-worse % below.
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

# Panel 1: average strokes over par
colors1 = ["#d62728" if v >= 1.5 else "#ff7f0e" if v >= 1.0
           else "#fdd835" if v >= 0.5 else "#2ca02c" for v in twin["avg_to_par"]]
ax1.bar(twin.index.astype(str), twin["avg_to_par"], color=colors1)
ax1.axhline(0, color="black", linewidth=0.5)
ax1.set_title(f"Twin Oaks GC: avg strokes over par by hole "
              f"(across {twin['rounds'].max()} rounds)")
ax1.set_ylabel("Avg strokes over par")
for i, (par, n, v) in enumerate(zip(twin["par"], twin["rounds"], twin["avg_to_par"])):
    ax1.text(i, v + 0.05, f"par{par}", ha="center", fontsize=8)

# Panel 2: double-bogey-or-worse frequency — "feels-like-a-nemesis" metric
colors2 = ["#d62728" if v >= 50 else "#ff7f0e" if v >= 35
           else "#fdd835" if v >= 20 else "#2ca02c" for v in twin["double_or_worse_pct"]]
ax2.bar(twin.index.astype(str), twin["double_or_worse_pct"], color=colors2)
ax2.axhline(50, color="red", linewidth=0.5, linestyle="--", label="50% line")
ax2.set_title("How often you make double-bogey or worse on each hole")
ax2.set_xlabel("Hole #")
ax2.set_ylabel("Double-bogey-or-worse %")
ax2.legend(loc="upper right")
for i, v in enumerate(twin["double_or_worse_pct"]):
    ax2.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=8)

plt.tight_layout(); plt.show()
"""),

    md(r"""
**Action plan.** Holes high on the **double-bogey-frequency** chart are
where pre-round visualization + a conservative game plan pay off most —
those are the holes that beat you up consistently. Holes high on the
**average** chart but moderate on double-bogey-frequency are blow-up holes
— a more aggressive plan with disciplined bail-out is the lever there.

Cross-reference with §1: if hole 3 is a double-bogey trap and you're hitting
mostly 7-iron/8-iron from the tee, the 125-150 yd approach SG leak is the
upstream cause. Fix the strike, fix the hole.
"""),

    md(r"""
## 5. Range (GC3) vs course (Arccos) — 7-iron comparison

Side-by-side distributions of your 7-iron from the launch monitor and from
real on-course shots. **Currently 7-iron only** because that's all the GC3
data we have. Adding sessions for other clubs is the path to expanding
this section.

**Unit caveat (important).** GC3 'Carry' is launch-monitor carry, no roll.
Arccos 'shot_distance_yd' is on-course total — carry + bounce + roll.
GC3's 'Total' uses a modeled roll that's *very* aggressive for irons (60+
yards on a 7-iron implies a hardpan bounce, not realistic green-holding).
Best comparison: **GC3 carry vs Arccos total minus ~7 yd of typical iron
roll** — the gap that remains is the on-course performance penalty (real
lies, wind, pressure swings, partial swings to specific yardages).
"""),

    code(r"""
res = dx.range_vs_course_7i(data)

# Stats table
stats_rows = []
for key in ("gc3_carry_stats", "gc3_total_stats", "arc_total_stats", "gc3_offline_stats"):
    s = res[key]
    if s["n"] == 0: continue
    stats_rows.append(s)
stats_df = pd.DataFrame(stats_rows).set_index("label")
stats_df
"""),

    code(r"""
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

# Panel 1: distance comparison (GC3 carry vs Arccos total)
bins = range(0, 180, 8)
axes[0].hist(res["gc3_carry"], bins=bins, alpha=0.55, color="#1f77b4",
             label=f"GC3 carry (n={len(res['gc3_carry'])})", density=True)
axes[0].hist(res["arc_total"], bins=bins, alpha=0.55, color="#d62728",
             label=f"Arccos total (n={len(res['arc_total'])})", density=True)
axes[0].axvline(res["gc3_carry"].median(), color="#1f77b4",
                linestyle="--", linewidth=2, alpha=0.8)
axes[0].axvline(res["arc_total"].median(), color="#d62728",
                linestyle="--", linewidth=2, alpha=0.8)
axes[0].set_title("7-iron distance: range CARRY vs course TOTAL")
axes[0].set_xlabel("Yards"); axes[0].set_ylabel("Density")
axes[0].legend()

# Panel 2: GC3 offline dispersion (range only — course can't measure this)
axes[1].hist(res["gc3_offline"], bins=range(-50, 51, 4), color="#2ca02c", alpha=0.7)
axes[1].axvline(0, color="black", linewidth=1)
axes[1].axvline(res["gc3_offline"].median(), color="red", linestyle="--",
                linewidth=2, label=f"median = {res['gc3_offline'].median():.1f} yd")
axes[1].set_title("7-iron offline dispersion (GC3 range; +R / -L)")
axes[1].set_xlabel("Yards left (-) or right (+) of target")
axes[1].set_ylabel("Shot count")
axes[1].legend()

plt.tight_layout(); plt.show()
"""),

    md(r"""
**How to read it.**

*Distance panel (left)*: the range carry (blue) being **right of** course
total (red) is the gap to close. Range carry of 122 yd median should be
roughly equivalent to course total of ~129 (carry + 7 roll). If course
total is well below that, you're losing distance on course beyond what
roll accounts for — pressure, partial swings, less-than-ideal lies.

*Offline panel (right)*: course Arccos can't easily measure "offline"
without knowing what you aimed at (the pin isn't always the target). The
GC3 offline distribution is the cleanest lateral-dispersion signal we
have. A median significantly left or right of 0 indicates a swing-path
bias — that's a range diagnostic that translates directly to on-course
misses on dogleg holes.

**Caveat.** GC3 sessions only have 7-iron right now. Adding more clubs
to the GC3 captures (driver, wedges) would let this section expand to a
true per-club range-vs-course comparison.
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
