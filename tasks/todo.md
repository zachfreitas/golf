# Golf Analysis — Todo

Live worklist for the project. Mark items `[x]` when shipped.

## Done

- [x] Initialize git, push existing GC3 work to https://github.com/zachfreitas/golf
- [x] Install `chrisdecali/golf-reports` and complete first Arccos sync (50 rounds, 3012 shots)
- [x] Build `arccos/loader.py` and `Arccos_Course_Analysis.ipynb` (4 sections)
- [x] Write `docs/USER_GUIDE.md` (comprehensive single doc)
- [x] Discover & document Arccos `isPaired` flag; loader now surfaces `paired_bag` from `_cache_raw/clubs_v6.json`
- [x] Correct clubType → label mapping (clubType 35 = 3 Hybrid; not in puller's CLUBTYPE map)
- [x] Recalibrate `forecast_club_distances.py` to use Smart Distance as the primary source with last-12-mo p80 cross-check
- [x] Document distance-metric distinctions (median vs p80 vs Smart Distance vs GC3 carry vs total) in USER_GUIDE §7
- [x] Diagnose loft-vs-swing question: distance progression issues at 7i/8i/PW are SWING-related, not loft-related → NO loft adjustments recommended
- [x] **Round 2 analyses**: extended loader (handicaps, per-round dash, course slope/rating), built `arccos/diagnostics.py` (4 functions), shipped `Arccos_Targeted_Diagnostics.ipynb`
- [x] Created `bag_inventory.csv` as authoritative bag source (14 in-bag + 3 owned-but-bench, with shaft/loft/measured carry/swing speed + data source provenance)
- [x] **Diagnostics §4 fix**: hole-by-hole heatmap now exposes median + double-bogey-or-worse % alongside avg-to-par. Hole 3 (median +2, 52% double+) correctly identified as a true nemesis even though it ranks 3rd on raw average.
- [x] **Diagnostics §5**: GC3 ↔ Arccos 7-iron range vs course comparison (`range_vs_course_7i`). Surfaces the ~16 yd on-course performance gap and the −7 yd left bias.
- [x] **Cheat-sheet recalibration**: `scripts/generate_cheat_sheet.py` now reads `data/bag_inventory.csv` for realistic distances (was using Tour-pro 2.3 yd/mph coefficient = +40-80 yd inflation). Added `Carry Ceiling` + `Total Ceiling` columns showing achievable improvement at current swing speed.
- [x] **Repo reorganization**: Moved root-level mess (22 files) into `data/`, `data/sessions/`, `outputs/`, `scripts/`, `notebooks/`. Scripts now use `REPO_ROOT = Path(__file__).resolve().parent.parent`; notebooks walk up to find `arccos`/`data`. Everything works from any cwd. Fixed pre-existing `asdfasfdfdff` typo in GC3 notebook cell-19.
- [x] **Scoring Method Level 1** — shipped `arccos/scoring_method.py`, `notebooks/Scoring_Method_L1.ipynb` (parameterized by `N` at top of setup cell), `outputs/scoring_method_L1.xlsx` (Summary + 30 per-round printable cards, chronological). **30-round read (2024-05-25 to 2026-06-26, 324 holes):** D3 rate 69%, zone-in-reg 34%, in-play 88%, bogey-ceiling 61%, blow-ups 32%. Total actual 1643 vs Robins-ceiling 1419 → **224 strokes available across the window**. Robins-lens diagnosis: full-swing get-to-100 + blow-up cascades. 5-round snapshot was noisier — 30-round window is the more reliable baseline.

## Decisions reached

- **Don't** drop the 4-hybrid or the 5-iron. Both doing real work (Smart Distance 166 / 153, 12-13 yd gap). The "overlap" call earlier was based on raw shot medians, which were misleading.
- **Drop the 9-iron.** Smart Distance 108 vs PW 107 — true 1-yd overlap. PW wins on spin / stopping power.
- **Don't add an 11-wood.** Loft (~29°) overlaps with existing 6-iron (29°) which is the user's most-efficient iron.
- **Don't add a 50° wedge** (user veto, even though it'd fix the PW→GW 24-yd gap textbook-style).
- **9-wood (~25° loft) is a defensible add** if replacing the 4-hybrid 1-for-1 for trajectory/forgiveness. But analysis says no bag move is needed before fixing iron contact.
- **No loft adjustments to irons.** Lofts are ~stock P770; progression is healthy. The 7i/8i/PW clustering is a contact-quality issue, not a loft issue.

## Open

### Bag
- [ ] Decide whether to drop the 9-iron (recommended). One-time decision; no cost.
- [x] Capture measured **driver** swing speed on the GC3 — measured 83.9 mph avg (range 81-87 mph) on 2026-06-30; Book1 estimate of 84 mph was accurate
- [x] Capture measured **5-iron** swing speed on the GC3 — measured 77.0 mph avg on 2026-06-30
- [ ] Capture measured **3W, hybrid, wedge** swing speeds — top + bottom of bag are the least confident in the forecast
- [ ] **NOTE — 2026-06-30 Driver + 5i session**: user flagged this as a bad day; data in sessions but treat as a baseline/outlier floor, not representative peak. Get a second session to triangulate.
- [ ] Per-wedge gapping session with launch monitor — three MG4 wedges share generic `Wedge` label in shots.csv, so per-wedge p80 isn't disambiguated by Arccos data alone

### Practice priorities (in order of stroke ROI)
- [ ] **Short putts 5-12 ft** — diagnostics §2 confirms this is the putting leak. Tour makes 33-58% in this range; you make 17-25%. 1 hour/week of straight-line drills.
- [ ] **Par-3 tee shots in 125-150 yd range** — diagnostics §1 shows tee lie loses 0.57 SG/shot, worst lie in this band. Practice 7i / 6i full swings from a mat to a target.
- [ ] **7i / 8i strike improvement on the GC3.** Lift smash 1.31 → 1.35 to attack the 125-150 yd approach SG leak (−0.42 SG/shot, biggest single bleed at ~73 strokes over 50 rounds)
- [ ] Consider lessons specifically targeting iron contact + spin (current 7i spin 4924 vs target 6500-7500)
- [ ] **Test grip strength hypothesis**: 2026-06-30 session shows 5i best strikes at 2,499–3,299 rpm (target 5,500–6,500) and driver at 1,075–1,649 rpm on several shots — well below target. Strong grip closing the face is one plausible cause (reduces spin loft). Test: hit a GC3 session with a deliberately weakened grip and compare spin rates on best strikes vs this baseline.
- [ ] Hole 1 + hole 9 at Twin Oaks (your worst at +1.58 / +1.52 to par) — pre-round visualization + clear strategy

### Scoring Method Level 1 — Zone-in-Reg practice plan
Diagnostic (30-round window): 14% zone-in-reg on par-4s, 21% on par-5s. Par-3s are fine (95%). Driver Smart Distance 217 yd is ~7 yd short of what's needed to reach the 100-yd zone on the average 324-yd Twin Oaks par-4. On-course decision-making has higher ROI than swing work here.

**On-course strategy (zero practice — start next round):**
- [ ] **Every par-4/5 tee: name the shot's purpose OUT LOUD before swinging.** "Reach zone" or "set up zone in 2". If you can't reach zone with this club on this hole, plan the 2-shot sequence. Robins' rule: play the game, not the shot.
- [ ] **Par-5 3-shot sequence at Twin Oaks (avg 473 yd)**: driver (217) + 4-hybrid (166) = 383 yd traveled, 90 yd remaining → inside the zone in 2. Currently only 21% of par-5s hit this — that's the target %.
- [ ] **Par-4 under 320 yd**: driver is the correct club. Under 300, take 3W or 3H to guarantee in-play (fairway > 20 yd extra distance for the L1 game).
- [ ] **Par-4 over 350 yd**: accept bogey-ceiling target (2 strokes to zone). Don't over-swing driver trying to reach — you're 7 yd short even flushed. Play 3W tee + full 7i/6i to zone.

**Purposeful-practice range drills (30-min sessions, once a week):**
- [ ] **Driver corridor test — 20 balls to a 30-yd-wide corridor.** Pass = 15/20 in the corridor. Fail = driver stays in the bag on tight par-4s until you re-test and pass. Track pass/fail per session in `data/sessions/`.
- [ ] **Hybrid + 3W corridor test — same rules, 25-yd corridor.** These are your reliability-off-the-tee clubs. If they can't hit the corridor, the whole strategy above collapses.
- [ ] **"Zone-entry" 6i/7i drill — 10 balls to a 130-yd target.** Success = ends <20 yd wide of target. This is your zone-setting-approach shot after a driver on a 350-yd par-4.

**Mindset (Robins' Key 2 — golfing mindset):**
- [ ] **After any bad shot, drop one level.** If you were going for the green (Level 4), reset to "get inside 50" (Level 2). If that fails, "get inside 100" (Level 1). Kill the compounding — 32% blow-up rate is the price of chasing after a bad shot.
- [ ] **Pre-round: pick one L1 metric to focus on for the whole round.** Zone-in-reg, or in-play %, or bogey-ceiling. Track manually on the scorecard. Trying to fix everything = fix nothing.

### Upstream / tooling
- [ ] Open upstream PR on `chrisdecali/golf-reports` for the `None`-hole patches in `pull_arccos.py` (lines 530, 637)
- [ ] Open upstream PR adding clubType 35 to `CLUBTYPE` map (and any other types we discover) — currently surfaces as "Club 35" in shots.csv

### Analysis
- [ ] Update `Arccos_Course_Analysis.ipynb` to use the new `paired_bag` + `shots_in_bag()` filters so the notebook automatically excludes retired-club shots
- [ ] Track per-round SG totals in a weekly rolling chart once `>5` rounds played in 2026
- [ ] Course-specific analysis once enough rounds played per course (Twin Oaks GC dominates the dataset)
- [ ] **Scoring Method Level 2/3/4** — extend `arccos/scoring_method.py` with L2 (inside 50 yd, down-in-2), L3 (inside 25 yd, up-and-down conversion), L4 (GIR + first-putt proximity + 3-putt avoidance). Same shape as L1: per-hole metrics -> per-round scorecards -> aggregate + practice priorities.
- [ ] After a few more rounds, rerun L1 with N=10 to see whether the "get-to-zone 31%" number holds (small-sample: 49 holes across 5 partial rounds)

## Maybe later

- [ ] Auto-pull Arccos via cron / Windows Task Scheduler after each round
- [x] Side-by-side range vs course dispersion chart (7-iron only for now — `diagnostics.range_vs_course_7i()` + Targeted Diagnostics §5). Expanding to other clubs needs GC3 sessions for those clubs.
