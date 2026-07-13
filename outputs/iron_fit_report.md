# Iron Fit Analysis — Zach Freitas

**Date:** 2026-07-13
**Method:** Maltby Playability Factor (MPF) "preference fingerprint" from your favorite
irons, ranked against every current-market (2023+) iron, cross-referenced with your
on-course distance data.

---

## ⚠️ MAJOR REVISION after your GC3 data (read this first)

Your GC3 numbers changed the recommendation. The problem isn't forgiveness or distance —
it's **low spin, low height, and shallow descent: your irons don't hold greens** (details
below). That reframes the whole search:

> **The forgiveness-first pick (P790) is the WRONG answer for your actual problem.**
> The Golf Digest 2026 robot tests show the "players-distance" category — P790 (4,911 rpm),
> Ping i540 (4,429), PXG 0311P (4,919) — is **deliberately LOW-SPIN with shallow descent.**
> Those irons would make your green-holding problem *worse*, even though they're forgiving.

> **New top pick: Ping i240** — high spin (5,662 rpm), steep descent (45.6°), high peak,
> the **weakest loft in class (30° 6i = more spin/height)**, AND genuinely forgiving for a
> players iron (Maltby MOI 15.8, well above your P770's 11.5). It directly attacks your
> spin/height/descent deficit while keeping the consistency you value.

**Also strong for your launch problem:**
- **TaylorMade Qi4D Max HL** (game-improvement, *same brand as your bag*): high-launch by
  design — 5,843 rpm, 45.9° descent, forgiving. The "HL" is built for exactly your issue.
- **Ping G740** — maximum forgiveness (MOI 18.9) with better launch than P790.
- **Wilson Staff Dynapwr** — high spin (5,604) + steep descent (45.8°) in a forgiving head.
- **Mizuno Pro M-13 / S-1** — most spin/steepest, but less forgiving (players profile).

Full launch-first ranking: `outputs/iron_fit_for_launch.csv`.
The original MPF forgiveness analysis (below) still stands as *one* lens — but your launch
data says prioritize **spin + descent + high launch**, not low-spin distance.

---

## (Original) MPF forgiveness recommendation

> **Forgiveness-only pick: TaylorMade P790 (2024)** — fit score 98.5/100 on the Maltby
> forgiveness lens, same TaylorMade family, great distance consistency. **BUT** see the
> revision above — P790 is low-spin and does not address your green-holding problem.

**Forgiveness runners-up:** Mizuno JPX 925 Hot Metal Pro, Titleist T250, Cobra Dark Speed.

---

## Note: Maltby TS3 Forged DBM (a component-head option)

Another analysis recommended the **Maltby TS3 Forged DBM** — it's a sound call, consistent
with this one. adj VCOG −0.072 (launches higher for its loft than your P770's −0.044), loft
28° (not jacked, preserves spin), MPF 850 (far more playable than your P770's 567). As a
GolfWorks component head it's cheap and fully custom — ideal for a **graphite MMT 75 S,
gap-matched** build (your consistency priority).

Caveats vs the picks below: MOI 12.3 is only modestly above your P770 (11.54) and below the
forgiveness leaders (i240 15.8, Staff Dynapwr 16.5); and Maltby heads have **no independent
robot spin/descent data** (green-holding is inferred from CG, not measured).

If going the Maltby/component route, also look at the **TS3.5 Forged** — lowest adj VCOG in
the Maltby line (−0.100), the closest modern iron to your all-time X-20 Tour (−0.148), so it
may fix your low-launch flaw even better.

---

## Best recent replacement per BRAND (matched to your flaws)

Balancing your two needs — spin/launch (to hold greens) AND forgiveness. Blades excluded.
Numbers: Golf Digest 2026 robot (7i @82mph) unless marked MGS (MyGolfSpy).

| Brand | Pick | spin / descent | Why | Alt |
|---|---|---|---|---|
| **TaylorMade** (your bag) | **Qi4D Max HL** '26 | 5,843 / 45.9° | Highest-spin, steepest GI iron; high-launch by design; same brand | P790 (players look, low-spin) |
| **Ping** | **i240** '26 | 5,662 / 45.6° | MOI 15.8, tightest dispersion — spin + forgiveness | G740 (MOI 18.9, less spin) |
| **Wilson** | **Staff Dynapwr** '26 | 5,604 / 45.8° | Highest peak (88 ft), MOI 16.5, strong spin | — |
| **Callaway** | **Apex Ti Fusion** '25 | 5,557 / 45.6° | Most spin of Callaway's forgiving irons; P770-like look | Apex Ai200 (more forgiving) |
| **Cobra** | **3DPx** '26 | 5,387 / 44.5° | Forgiving GI + solid spin | 3DP Tour (more spin, less forgiving) |
| **Mizuno** | **JPX 925 Hot Metal Pro** | ~5,400 | Forgiving hot-metal, clean look | Pro M-13 (5,894 spin, less forgiving) |
| **PXG** | **0311P Gen 8** '26 | 4,919 / 45.4° | Forgiving hollow (MOI 14.5), steep descent | 0311XP (more forgiving, lower spin) |
| **Titleist** | **T150** (MGS) | 5,734 / 45.9° | Best Titleist for your launch flaw | T200/T350 (forgiving but low-spin) |
| **Srixon** | **ZXi4** '25 | ~5,000 | GI, higher launch/forgiveness | ZXiR HL (max launch, SGI) |

**Across all brands: Ping i240** (spin + forgiveness + tightest dispersion).
**Same-brand continuity: TaylorMade Qi4D Max HL.** Build in graphite (MMT 75 S), fit to
preserve carry gaps.

---

## Best recent replacement per band (matched to your flaws)

Your flaws (low spin / height / descent; want forgiveness + tight gapping; players look;
graphite MMT 75 S; TaylorMade bag). Data: Golf Digest 2026 robot (7i @82mph) + Maltby MOI;
SGI from MyGolfSpy. Full table: `outputs/iron_unified_comparison.csv`.

| Band | Pick | Robot (spin / descent / peak) | MOI | Why for you |
|---|---|---|---|---|
| **Players** ⭐ | **Ping i240** (2026) | 5,662 / 45.6° / 85 | 15.8 | Tightest dispersion in class (137 sq ft), most forgiving players iron, weak loft = more spin/height. Best overall fix. |
| **Players Distance** | **Callaway Apex Ti Fusion** (2025) | 5,557 / 45.6° / 86 | 13.0 | Most spin + steepest descent of the distance irons (closest to your P770 lane). |
| **Game Improvement** | **TaylorMade Qi4D Max HL** (2026) | 5,843 / 45.9° / 84 | — | Purpose-built high launch, forgiving, same brand. Co-leader: Wilson Staff Dynapwr (5,604 / 45.8° / 88, MOI 16.5). |
| **Super Game Improvement** | Srixon ZXiR HL / Tour Edge Hot Launch Max D | ~5,000 / ~41° | high | Max launch+forgiveness, but likely more iron than you want. |

**Bottom line: Ping i240** is the single best replacement — a players iron that launches high,
spins, lands steep, AND is the most forgiving/consistent in its class. Stay-in-lane pick:
Callaway Apex Ti Fusion. Max-forgiveness/brand-continuity pick: TaylorMade Qi4D Max HL.
Always: build in graphite (MMT 75 S) and fit to preserve your carry gaps.

---

## Your GC3 launch diagnosis + the VCOG / MOI answer

Robust medians from your GC3 sessions (well-struck shots only):

| Club | n | club mph | smash | launch | **spin** | **peak (ft)** | **descent** | carry |
|---|---|---|---|---|---|---|---|---|
| 5-iron | 14 | 76 | **1.40** ✓ | 14.3° | **2,826** ✗ | 46 ✗ | 29.5° ✗ | 149 |
| 7-iron | 67 | 75 | 1.31 ✓ | 18.8° | **4,949** ✗ | 61 ✗ | 39.5° ✗ | 133 |

(green-holding windows for your speed: 7i spin ~5,500–6,800, descent ~45–50°, peak ~82–100 ft)

**Diagnosis:** your **strike is excellent (smash 1.40 / 1.31) and carry is fine.** The
deficit is entirely **spin, peak height, and descent angle** — your ball flies low and hot
and won't stop on greens. Your AoA is descending and appropriate, so this is **not** a swing
fault; it's the club's **CG/spin character.**

**Do you need a different VCOG or MOI? Yes — here's the data:**

The right CG figure is **Effective VCOG = Basic VCOG + Adjusted VCOG** (the "Adjusted"
column is a loft correction you ADD to the basic measured VCOG — not used alone). Lower
effective VCOG = launches higher. We also use **RCOG** (CG depth; deeper = more launch +
MOI) — the third lever you flagged.

| Iron | 6i loft | Basic VCOG | + Adj | **= Effective VCOG** | **MOI** | **RCOG** (depth) |
|---|---|---|---|---|---|---|
| **X-20 Tour** (your #1 all-time) | 30° | 0.860 | −0.148 | **0.712** | **13.71** | **0.753** (deep) |
| **P770 (your gamer)** | 29° | 0.788 | −0.044 | **0.744** | **11.54** | 0.516 |

Your favorite iron ever had a **lower effective VCOG (0.712 vs 0.744 → higher launch),
higher MOI (13.71 vs 11.54), and a much deeper CG (RCOG 0.753 vs 0.516)** — a high-launch,
forgiving design. Your P770 sits higher/shallower on all three, which is exactly why your
ball flies low with little spin.

**What to change (target ≈ your X-20 Tour):**
1. **Lower effective VCOG (≤ ~0.71)** → raises launch and peak height.
2. **Deeper CG (higher RCOG) + higher MOI** → more launch, more forgiveness, holds ball
   speed on misses (your consistency love).
3. **Do NOT chase stronger lofts** → strong lofts kill spin, worsening green-holding. This
   is why low-spin players-distance irons (P790/i540) are the wrong tool for *you*.

**Important nuance:** effective VCOG predicts launch ANGLE, not SPIN — the P790 has the
lowest effective VCOG (0.693) yet the lowest robot spin (4,911). So the full fix pairs a
low effective VCOG with **measured robot spin/descent** (the green-holding half).

**On "normalizing to loft":** you were right to question a home-brew — Maltby already bakes
the loft correction into the Adjusted column, so **Effective = Basic + Adjusted** is the
loft-correct CG. Columns `vcog_eff`, `rcog`, `moi` and deltas-vs-P770 are in
`outputs/iron_unified_comparison.csv` and `outputs/iron_fit_for_launch.csv`.

**Charts (`outputs/charts/`):**
1. `1_cg_map.png` — Effective VCOG (launch) vs RCOG (depth), bubble = MOI; your P770,
   X-20 Tour and X-22 Tour marked, target zone shaded.
2. `2_green_holding.png` — robot spin vs descent angle; your P770 sits alone in the
   low-spin/shallow corner.
3. `3_spin_vs_moi.png` — spin vs MOI: your two needs on one plot, sweet spot upper-right.

---

## The key insight (forgiveness lens)

Your three favorite irons, scored on the Maltby Playability Factor (higher MPF = more
forgiving/playable):

| Rank | Iron | Year | **MPF** | Category |
|:---:|---|:---:|:---:|---|
| #1 all-time | Callaway **X-20 Tour** | 2007 | **716** | Super Game Improvement |
| #2 / gamer | TaylorMade **P770** | 2023 | **567** | Game Improvement |
| #3 | Callaway **X-22 Tour** | 2009 | **594** | Game Improvement |

**Your favorite iron ever (X-20 Tour, 716) is ~150 MPF points MORE forgiving than the
P770 you play now (567).** That's a big gap — roughly the difference between a "players
distance" iron and a compact players iron.

This matters because everything in your game file points the same direction:
- **125–150 yd is your worst approach zone** — that's your 5i/6i/7i (153/141/129 yd),
  the exact clubs where more forgiveness pays off most.
- **Zone regulation caps at 33%** and dispersion is your limiter (7i ~96 yd spread),
  not distance.
- You explicitly value **distance consistency** — which forgiveness (higher MOI, lower
  CG, hotter face) directly improves on mishits.

**Conclusion:** you've been gaming your *least* forgiving favorite. Moving back toward
the X-20 Tour's forgiveness level (~700 MPF) with a modern players-distance iron fits
your proven preferences *and* your skill profile. Not because the P770 is "wrong" — but
because your own history says you score better with more help.

---

## Ranked shortlist (current irons, with specs)

Fit score peaks at ~700 MPF (your X-20 Tour level) and rewards the whole preferred band
(590–740). "vs P770" = MPF points more forgiving than your current gamer.

| # | Iron | Year | MPF | vs P770 | Fit | 7i loft* | Construction | Consistency |
|:--:|---|:--:|:--:|:--:|:--:|:--:|---|:--:|
| 1 | **TaylorMade P790** | 2024 | 697 | +130 | **98.5** | 30° | Hollow forged + SpeedFoam Air + tungsten | Excellent |
| 2 | Mizuno JPX Hot Metal Pro | 2023 | 696 | +129 | 98.0 | ~31° | One-piece Chromoly | Excellent |
| 3 | Titleist T250 | 2025 | 690–693 | +123 | 95–96 | 31° | Forged face + tungsten | Excellent |
| 4 | Mizuno JPX 925 Hot Metal Pro | 2025 | 713 | +146 | 93.5 | 31° | One-piece Chromoly, clean profile | Excellent |
| 5 | Cobra Dark Speed | 2024 | 713 | +146 | 93.5 | ~30° | Hollow, PWR-Bridge, tungsten | Very good |
| — | **P790 Forged / P770 replacement tier ↓** | | | | | | | |
| 6 | TaylorMade P790 Forged | 2025 | 676 | +109 | 88.0 | 30.5° | Forged players distance | Excellent |
| 7 | Titleist T150 | 2025 | 641 | +74 | 70.5 | 32° | Forged, strong-loft players | Very good |
| 8 | Mizuno JPX 923 Forged | 2023 | 637 | +70 | 68.5 | 34° | Grain-flow forged Chromoly | Very good |
| 9 | TaylorMade P770 (2025) | 2025 | 645 | +78 | 72.5 | 33° | Compact hollow forged | Excellent |

\* *Lofts are manufacturer-published references; exact numbers should be confirmed at
fitting (see Data notes). Your P770 7i loft (33°) is from your own bag file.*

Full ranking of all 119 current irons: `outputs/iron_fit_recommendations.csv`
Enriched shortlist: `outputs/iron_fit_shortlist_enriched.csv`

---

## Why the P790 specifically

1. **Forgiveness = your happy place.** MPF 697 ≈ your X-20 Tour (716). You've *proven*
   you play your best golf at this forgiveness level.
2. **Brand + feel continuity.** Your entire bag is TaylorMade (Qi10 driver/woods/rescues,
   P770 irons, MG4 wedges). The P790 is the P770's more-forgiving sibling — same
   hollow-body/SpeedFoam/tungsten DNA, so the look, sound, and feel carry over.
3. **Distance consistency** — the trait you called out. The P790 is the category
   benchmark for tight, repeatable carry numbers on mishits, which should help your
   inconsistent mid-iron gaps (your 7i→ next gap is TIGHT at 4 yd, PW gap is WIDE at
   24 yd — a re-gapping opportunity).

### Combo-set option (worth a fitting conversation)
Because the P790 and your P770 are designed to blend, a common setup is **P790 in the
long/mid irons (4–7)** — where forgiveness helps your 125–150 zone most — and **P770 in
the scoring irons (8–PW)** where you want control. That keeps the compact look where it
matters and adds help where you need it.

---

## ⚠️ Gapping caution (because you value consistency)

Modern players-distance irons are **stronger-lofted** than your P770. Authoritative
TaylorMade stock lofts (Custom Component Booklet, updated 06/03/26):

| Iron | P770 (gamer) | P790 | Δ |
|:--:|:--:|:--:|:--:|
| 5 | 25.5° | 23° | −2.5° |
| 6 | 29° | 26.5° | −2.5° |
| **7** | **33°** | **30°** | **−3°** |
| 8 | 37° | 34° | −3° |
| 9 | 41° | 39° | −2° |
| PW | 45–46° | 44° | −1 to −2° |

The P790 is a full **3° stronger at the 7-iron**, which adds roughly **half a club of
distance** across the set — your 7i could jump from ~129 to ~135+ yd. That's not
automatically good: it can re-open the tight gaps you love and push your longest iron
too far.

**Good news:** TaylorMade publishes an **official P-Series combo gapping chart** (same
booklet, page 8) showing exactly how to bend each iron when mixing models "based on your
desired level of forgiveness." So a P790/P770 combo is a *supported, spec'd* build, not
a hack.

**Do not buy off-the-rack.** Get fit for lofts/lengths so the new set *preserves* your
current gapping (your P770 gaps are dialed: 5i→6i 12, 6i→7i 11, 8i→9i 16). Ask the
fitter to match your carry ladder, not just hand you stock lofts.

---

## All data sources integrated (`data/irons_research/`)

| Source | File | What it adds |
|---|---|---|
| GolfWorks Maltby (master) | `maltby_mpf_irons.csv` | 1,124 irons, playability score + category |
| GolfWorks Maltby (per-brand) | `maltby_mpf_brand_specs.csv` | 1,086 irons w/ **loft, MOI, VCOG, adj-VCOG, CG depth** |
| Golf Digest 2026 robot | `golfdigest_robot_2026.csv` | 26 irons (7i @82mph): **spin, dyn loft, descent, peak, carry, dispersion** |
| Cool Clubs 2026 robot | `coolclubs_iron_data.csv` | Ping/Wilson/Callaway/Cobra/Mizuno (7i @80mph, steel): launch, spin, peak, descent, shot area |
| MyGolfSpy 2026 robot | `mygolfspy_robot.csv` | 45 irons w/ **ball speed**, carry, launch, spin, peak, descent, shot area |
| MyGolfSpy 2026 scores | `mygolfspy_scores.csv` | 74 irons: independent MGS / Accuracy / Distance / Forgiveness scores |
| Your GC3 | `outputs/gc3_launch_diagnostic.csv` | your measured launch profile (the diagnosis) |

**Caveat:** the three robot sources use different conditions (Golf Digest 82 mph stock
shafts; Cool Clubs 80 mph steel KBS; MyGolfSpy varies by guide) — compare *within* a
source, not across. Peak height units differ (GD/Cool Clubs feet; MyGolfSpy yards).

## Data notes & provenance

- **Core dataset (rock-solid):** GolfWorks Maltby Playability Factor master chart —
  1,124 irons, 61 brands, MPF −873 to 1328. Parsed directly from the source PDF; every
  row's category was verified against Maltby's published score bands (0 mismatches).
  Rebuild anytime with `python scripts/build_maltby_mpf_dataset.py` (it checks for chart
  updates and new brand PDFs before doing anything).
- **Your numbers (rock-solid):** favorites, P770 lofts, and on-course carries are from
  your own files.
- **TaylorMade specs (authoritative):** P770/P790 lofts and the combo gapping chart are
  from TaylorMade's Custom Component Booklet (updated 06/03/26), fetched directly:
  `https://www.taylormadegolf.com/on/demandware.static/-/Sites-tmag-custom-catalog-us/en_US/v1783915569976/pdf/Custom_Shafts.pdf`
- **Other brands' specs (directional):** live fetches from MyGolfSpy, GOLF RoboTest,
  Cool Clubs, and most manufacturer product pages were **blocked by bot protection**, and
  `WebSearch` is disabled in this environment, so I couldn't auto-discover the equivalent
  spec PDFs for Titleist/Mizuno/Callaway/PXG/Cobra/Srixon. Those brands publish similar
  spec sheets — **if you paste the URLs (like you did for TaylorMade), I'll ingest them
  the same way** and upgrade those rows to authoritative. Until then, their
  loft/construction columns are established published specs + reviewer consensus — confirm
  at fitting.
- **Why MPF carries the analysis:** the Maltby Playability Factor is an engineering-derived
  metric computed from measured head geometry (CG, MOI, face flex, etc.), so it already
  captures most of what robot *forgiveness* tests measure — which is why the ranking is
  solid even without per-model robot numbers.
