# Golf Analysis — Todo

Live worklist for the project. Mark items `[x]` when shipped.

## Done

- [x] Initialize git, push existing GC3 work to https://github.com/zachfreitas/golf
- [x] Forecast realistic per-club distances anchored to measured 7i (74.8 mph → 127 yd)
- [x] Install `chrisdecali/golf-reports` and complete first Arccos sync (50 rounds, 3012 shots)
- [x] Build `arccos/loader.py` and `Arccos_Course_Analysis.ipynb` (4 sections)
- [x] Write `docs/USER_GUIDE.md` (comprehensive single doc per CLAUDE.md convention)

## Open

- [ ] Capture measured **driver** swing speed on the GC3 (currently forecast at 84.8 mph, untested)
- [ ] Capture measured **3W, hybrid, wedge** swing speeds (forecast accuracy degrades away from the 7i anchor)
- [ ] Decide on the **4H vs 5i overlap** (both forecast 143 yd carry; possibly drop one or bend a loft)
- [ ] Investigate the **PW → GW gap of 15 yd** — is a 50° wedge worth adding?
- [ ] Compare measured-on-course **125-150 yd approach SG (-0.42 / shot, n=175)** against range smash on 7i / 8i — biggest single leak in the bag
- [ ] Track per-round SG totals in a weekly rolling chart once `>5` rounds played in 2026
- [ ] Open upstream PR on `chrisdecali/golf-reports` for the `None` hole patch in `pull_arccos.py` (lines 530, 637)

## Maybe later

- [ ] Auto-pull Arccos via cron / Windows Task Scheduler after each round
- [ ] Side-by-side range vs course dispersion chart (one per club)
- [ ] Course-specific analysis once enough rounds played per course (>= 3)
- [ ] Compare wedge distances against GC3 wedge sessions (once collected)
