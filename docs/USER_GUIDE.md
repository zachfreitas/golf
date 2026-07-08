# Golf Analysis — User Guide

A personal golf-improvement workspace combining range data (Foresight GC3 launch
monitor) with on-course data (Arccos Caddie shot tracker) to find what to practice
and why. This is the single comprehensive doc for the project.

## Table of contents

1. [What this repo is](#1-what-this-repo-is)
2. [File inventory](#2-file-inventory)
3. [GC3 range workflow](#3-gc3-range-workflow)
4. [Arccos course workflow](#4-arccos-course-workflow)
5. [Combined workflow — range + course](#5-combined-workflow--range--course)
6. [Data schemas](#6-data-schemas)
7. [Distance metrics: which to use when](#7-distance-metrics-which-to-use-when)
8. [Current diagnostic findings](#8-current-diagnostic-findings)
9. [Troubleshooting](#9-troubleshooting)
10. [Maintenance](#10-maintenance)
11. [Targeted diagnostics notebook](#11-targeted-diagnostics-notebook)
12. [Scoring Method Level 1 workflow](#12-scoring-method-level-1-workflow)

---

## 1. What this repo is

### Repository layout

```
Golf_Analysis/
├── arccos/          Python package: loader.py + diagnostics.py
├── data/            Input source-of-truth (don't regenerate)
│   ├── bag_inventory.csv   (current bag, with In-Bag/Bench flag)
│   ├── Book1.xlsx          (bag specs for the cheat-sheet generator)
│   └── sessions/           (raw GC3 session CSVs as you record them)
├── outputs/         Derived artifacts (regenerable from scripts)
│   ├── GC3_Launch_Monitor_Cheat_Sheet.xlsx
│   ├── per_club_on_course.csv
│   ├── personalized_targets.csv
│   ├── session_progress.csv
│   ├── summary_stats.csv
│   └── summary.txt + final_summary.txt
├── scripts/         Runnable .py files (always invoke from repo root)
│   ├── forecast_club_distances.py
│   ├── generate_cheat_sheet.py
│   ├── build_notebook.py
│   └── build_diagnostics_notebook.py
├── notebooks/       Jupyter notebooks
│   ├── GC3_Golf_Analysis.ipynb
│   ├── Arccos_Course_Analysis.ipynb
│   └── Arccos_Targeted_Diagnostics.ipynb
├── docs/            This guide + archive/
└── tasks/           todo.md
```

**Convention**: scripts and notebooks all use `Path(__file__).resolve().parent.parent`
(scripts) or a walk-up-to-find-`arccos`/-`data` pattern (notebooks) to anchor
themselves to the repo root. That means you can run them from anywhere —
repo root, scripts/, notebooks/ — and paths still work.

### Two data sources, one improvement loop

- **Range data (GC3)** = controlled launch-monitor sessions. Reveals what the
  swing *can do* under ideal conditions. Captures club speed, ball speed, smash
  factor, launch angle, spin, attack angle, club path, dispersion.
- **Course data (Arccos)** = every shot you played on the course, GPS-tagged.
  Reveals what the swing *actually does* under pressure, on real lies, in real
  weather. Captures shot-by-shot distances, lies, strokes-gained vs scratch.

The repo ties them together: forecasts realistic per-club target distances from
your measured range data, compares those targets to your on-course reality, and
ranks practice priorities by strokes-lost per round.

---

## 2. File inventory

Every file committed to this repo, what it is, and when to use it.

### Range analysis (GC3 launch monitor)

| File | What it is | When to use |
|---|---|---|
| `notebooks/GC3_Golf_Analysis.ipynb` | Original notebook: 7-iron deep dive across 125 shots / 5 sessions. Dispersion maps, smash analysis, swing-flaw diagnosis, session-by-session trends. | Open after each new GC3 session to see how the latest practice changed your numbers. |
| `scripts/generate_cheat_sheet.py` | Reads `data/bag_inventory.csv` for realistic per-club distances + `data/Book1.xlsx` for swing speeds, writes `outputs/GC3_Launch_Monitor_Cheat_Sheet.xlsx`. Distance columns are **Current** (today's reality) and **Ceiling** (achievable with clean strike + optimized launch/spin). Launch/spin/smash targets are still computed from the legacy formula and remain valid aspirational range goals. | Run when bag changes or after a meaningful re-measurement on the GC3. |
| `data/Book1.xlsx` | Your bag specs: abbreviation, model, loft, shaft, **estimated** swing speed per club. Only 7-iron is measured. | Edit when shafts/lofts change. Note that `data/bag_inventory.csv` is the authoritative bag source now; Book1 lingers because the cheat-sheet script reads swing speeds from it. |
| `outputs/GC3_Launch_Monitor_Cheat_Sheet.xlsx` | Output of `scripts/generate_cheat_sheet.py` — print this and take it to the range. **Current vs Ceiling**: see [§7](#7-distance-metrics-which-to-use-when). | Range reference card. Earlier versions (pre-2026-06) had Tour-pro distance numbers — those were wrong; if you find a printed copy, throw it out and reprint. |
| `data/sessions/session_summary20260214.csv` … `20260302.csv` | Raw GC3 exports, one per session. Schema in [§6](#62-gc3-session-csv). | Source data for the GC3 notebook. Drop new ones in as you collect them. |
| `outputs/personalized_targets.csv` | One-row summary of your measured 7i vs target (current carry, target carry, smash, launch, spin). | Quick reference; expanded into the full per-club view by `scripts/forecast_club_distances.py`. |
| `outputs/session_progress.csv` | Across-session 7i trend (volume, smash, consistency, carry mean). | Track if range practice is actually moving the needle. |
| `outputs/summary_stats.csv` | Aggregated 7i statistics across all sessions. | Used by the GC3 notebook's "current state" cell. |
| `outputs/summary.txt`, `outputs/final_summary.txt` | Plain-text summaries auto-generated by earlier analysis runs. | Reference / human-readable status. |
| `scripts/forecast_club_distances.py` | Per-club distance reference for your **current paired bag**, prioritising Arccos Smart Distance (authoritative) with a recent-shots p80 cross-check column. Forecast/extrapolation only used when an in-bag club has zero Arccos data. | Run after each Arccos sync to see updated bag spacing + gap diagnostics. |
| `outputs/per_club_on_course.csv` | Output of the forecast script — Smart Distance, longest, recent p80, and gap-to-next-club for each club in your current paired bag. Columns in [§6.4](#64-per_club_on_coursecsv). | Reference when planning club selection or considering bag changes. |

### Course analysis (Arccos shot tracker)

| File | What it is | When to use |
|---|---|---|
| `arccos/loader.py` | Loads Arccos data from `~/golf-data/`: the four CSVs (`rounds_summary`, `holes`, `shots`, `clubs`) PLUS your **paired bag** (currently-in-bag clubs with authoritative Smart Distance) from `_cache_raw/clubs_v6.json`. One function: `load_arccos()`; helpers `paired_labels()` and `shots_in_bag()` filter retired clubs out of analysis. | Imported by the notebook and forecast script. Use directly to script your own analysis. |
| `arccos/__init__.py` | Re-exports `load_arccos` and `ArccosData`. | Convenience. |
| `notebooks/Arccos_Course_Analysis.ipynb` | The four-section course analysis: SG by category, per-club on-course carries, course-management decisions, practice priorities. Generated from `scripts/build_notebook.py`. | Open after each Arccos sync to see updated trends. |
| `scripts/build_notebook.py` | Source of truth for the Arccos notebook. Plain Python (diff-friendly); regenerates the .ipynb on demand. | Edit this, not the notebook, when adding/modifying analyses. |
| `arccos/diagnostics.py` | Targeted analytical helpers: 125-150 yd approach deep-dive, putt make-% by distance, lie-penalty matrix, Twin Oaks hole-by-hole. Imported by the diagnostics notebook. | Import directly if you want to slice the data yourself. |
| `notebooks/Arccos_Targeted_Diagnostics.ipynb` | Deep-dive notebook focused on the four highest-stroke-ROI questions. Generated from `scripts/build_diagnostics_notebook.py`. See [§11](#11-targeted-diagnostics-notebook). | Open when you want to decide what specifically to practice. |
| `scripts/build_diagnostics_notebook.py` | Source of truth for the diagnostics notebook. | Edit this, not the notebook, when modifying the deep-dives. |
| `arccos/scoring_method.py` | Will Robins Scoring Method Level 1 analysis module. Per-hole metrics: `in_play`, `strokes_to_zone`, `strokes_in_zone`, `zone_reached_in_reg`, `down_in_3`, `bogey_ceiling_met`, `blow_up`. Functions: `select_last_n_rounds`, `compute_hole_metrics`, `format_scorecard_df`, `aggregate_summary`, `score_if_bogey_ceiling_held`, `derive_practice_priorities`. See [§12](#12-scoring-method-level-1-workflow). | Import directly to script your own L1 slice, or run through the notebook. |
| `notebooks/Scoring_Method_L1.ipynb` | Per-hole scorecards + aggregate dashboard + Robins-lens practice-priority read over the last N rounds. Also produces `outputs/scoring_method_L1.xlsx` as a side effect. Generated from `C:/tmp/build_l1_notebook.py` — regenerate the notebook by running that script. | Open after every Arccos sync to see the L1 read on your most recent play. Change `N` at the top of the setup cell to rescope the window. |
| `outputs/scoring_method_L1.xlsx` | Excel workbook: Summary sheet + one printable per-round scorecard sheet per round in the lookback window. Color-coded Y/N cells for the four "did I meet the target" columns. | Print and mark up on the course, or reference during practice planning. |
| `data/bag_inventory.csv` | Authoritative bag inventory — every club you own, with `in_bag` flag distinguishing carried vs bench, plus shaft / loft / lie / measured carry / measured swing speed / data source. | Update when you add/swap a club; cross-check against Arccos `paired_bag` to confirm sensor pairings. |

### Project housekeeping

| File | Purpose |
|---|---|
| `README.md` | Quick reference; points here. |
| `LICENSE` | MIT. |
| `.gitignore` | Excludes credentials, raw Arccos cache (GPS + PII), notebook checkpoints, OneDrive sync detritus, Python venvs. |
| `requirements.txt` | Python deps for the notebooks + scripts in this repo (not the Arccos puller — that has its own requirements in `chrisdecali/golf-reports`). |
| `docs/USER_GUIDE.md` | This document. |
| `docs/archive/` | For superseded docs once anything in this guide is retired. |
| `tasks/todo.md` | Live worklist per the project convention in `CLAUDE.md`. |

---

## 3. GC3 range workflow

### One-time setup

```bash
pip install -r requirements.txt
```

### After every range session

1. **Export from GC3.** Open the FSX app on the GC3 device, finish the session,
   export the shot log to CSV. File should be named `session_summary<YYYYMMDD>.csv`.
2. **Drop it in the repo root.** No subfolder.
3. **Open `notebooks/GC3_Golf_Analysis.ipynb`** in VS Code or Jupyter. Run all cells. The
   notebook auto-discovers any `session_summary*.csv` and merges them.
4. **Read the diagnostic output.** The notebook flags your worst metric (today,
   that's smash factor 1.31 vs target 1.38). Use that as the focus for the next
   session.

### When something structural changes

- **New club** → update `data/Book1.xlsx` (add the row, swing speed estimate) AND
  add an `in_bag=1` row to `data/bag_inventory.csv` (with measured Smart Distance
  if Arccos has it after a few rounds, else leave blank to forecast). Then
  `python scripts/generate_cheat_sheet.py` to refresh the Excel cheat sheet.
- **Measured a new swing speed** → update both `data/Book1.xlsx` and the matching
  row in `data/bag_inventory.csv` (`swing_speed_mph` column). For 7-iron only,
  also update `MEASURED_7I_SPEED` and `MEASURED_7I_CARRY` references in
  `scripts/forecast_club_distances.py` (the GC3 anchor). Then rerun
  `python scripts/forecast_club_distances.py` and `python scripts/generate_cheat_sheet.py`.
- **Sync a fresh Arccos round** → after `pull_arccos.py`, Smart Distance for
  every paired club refreshes in `_cache_raw/clubs_v6.json`. Rerun
  `python scripts/forecast_club_distances.py` to update `outputs/per_club_on_course.csv`
  and `python scripts/generate_cheat_sheet.py` to refresh the cheat sheet with
  the latest Smart Distance numbers (note: cheat sheet currently reads
  carries from `data/bag_inventory.csv`, not Smart Distance directly — update
  the inventory CSV first if you want the cheat sheet to reflect a new
  Smart Distance reading).

### What the GC3 notebook tells you

- **Shot dispersion map** — bird's-eye view of every shot vs target zone.
- **Smash factor vs spin** — where you're losing ball speed.
- **Attack angle vs launch angle** — strike-quality diagnostic.
- **Ball speed vs club speed** — energy transfer efficiency.
- **Session-by-session progress** — 4-panel trend (carry, smash, consistency, volume).
- **Swing-flaw diagnosis** — prioritized list of fixable issues with severity.

---

## 4. Arccos course workflow

The Arccos puller is **not in this repo** — it lives in
[`chrisdecali/golf-reports`](https://github.com/chrisdecali/golf-reports), a
separate tool that handles auth + sync. This repo only contains the analysis
layer that reads the puller's output.

### One-time setup

```bash
# 1. Clone the upstream Arccos tool somewhere outside this repo
git clone https://github.com/chrisdecali/golf-reports.git ~/tools/golf-reports

# 2. Install its dependencies
cd ~/tools/golf-reports
pip install --user -r requirements.txt

# 3. Authenticate + first sync (this prompts you for Arccos email/password;
#    password is sent once to api.arccosgolf.com, then discarded; only the
#    long-lived access key is stored at ~/.arccos_creds.json, chmod 600)
GOLF_INCLUDE_GPS=1 python setup.py
```

The `GOLF_INCLUDE_GPS=1` env var is what makes the sync pull shot GPS
coordinates (needed for the on-course distance analysis and any shot-map
rendering). Without it, you'll still get SG categories but lose the spatial
analysis.

#### Known upstream bugs (patched locally)

1. **`None` holes crash the build.** The version of `pull_arccos.py` shipped
   at the time of writing crashes when a round contains a `None` hole (some
   9-hole rounds or imported rounds trigger this). Two-line defensive patch:
   - `ingest/pull_arccos.py:530` — add `if not isinstance(h, dict): continue`
     before the inner shot loop in `build_clubid_map`.
   - `ingest/pull_arccos.py:637` — change `holes = [h for h in (detail.get("holes") or []) if h.get("shouldIgnore") != "T"]`
     to `holes = [h for h in (detail.get("holes") or []) if isinstance(h, dict) and h.get("shouldIgnore") != "T"]`.

2. **`clubs.csv` mixes paired + unpaired clubs.** Arccos's v6 API splits
   clubs into `paired` (currently in your bag) and `unpaired` (retired) — see
   `_cache_raw/clubs_v6.json` — but `pull_arccos.py` dumps both into
   `clubs.csv` without distinction. Without filtering, old 5-woods and
   retired sensors leak into per-club analysis. Our `arccos/loader.py`
   provides a `paired_bag` DataFrame and `shots_in_bag()` helper that filter
   to currently-paired clubs only. Use those, not raw `clubs.csv`.

3. **`clubType` 35 missing from puller's `CLUBTYPE` map.** Falls back to the
   generic label "Club 35" in `shots.csv`. Our loader knows it's the 3-hybrid
   (TaylorMade Qi10 Rescue 19°) and surfaces it as such via the `label` field
   in `paired_bag`. When joining `paired_bag` to `shots.csv`, use
   `shots_csv_label` for matching and `label` for display.

If you ever `git pull` the upstream tool, reapply patches 1 & 2 or open a PR.

### After every round

The Arccos app syncs the round to the cloud automatically. To pull it locally:

```bash
cd ~/tools/golf-reports/ingest
GOLF_STORE=~/golf-data GOLF_INCLUDE_GPS=1 python pull_arccos.py --include-gps
```

This re-fetches changed data, rebuilds the CSVs in `~/golf-data/`. Rate-limited
(600s between syncs) — don't loop on it.

Then in this repo:

```bash
cd <path-to>/Golf_Analysis
python scripts/build_notebook.py                                # regenerate the notebook source
jupyter nbconvert --to notebook --execute --inplace \
        notebooks/Arccos_Course_Analysis.ipynb                  # rerun all cells with new data
```

Or just open the notebook in Jupyter and **Run All**.

### What the Arccos notebook tells you

- **Section 1 — SG by category over time**: rolling 5-round trend chart in each
  of off-tee, approach, short game, putting. The single most important page;
  shows whether practice is *actually* improving anything.
- **Section 2 — Club carry & dispersion on-course**: per-club median + 80% band
  from real shots, side-by-side with the forecast from `scripts/forecast_club_distances.py`.
  Large `Delta vs forecast` (negative) = on-course is materially shorter than
  the range; that's the gap practice has to close.
- **Section 3 — Course management**: tee-club SG (which clubs save vs lose
  strokes off the tee) + approach SG by distance bucket (where you bleed the
  most). The current data shows 125-150 yd is your single biggest leak.
- **Section 4 — Practice priorities**: each category's strokes-lost-per-round,
  with a recommended practice-time share. Approach dominates at 38%.

---

## 5. Combined workflow — range + course

The two sources answer different questions; cross-referencing them is where
improvement comes from.

| When you see this on the range… | …check on the course… | …because |
|---|---|---|
| Smash factor below target | Are mid-iron approach SGs bleeding? | Low smash = inconsistent contact = unreliable distance = approach SG losses. |
| Wide dispersion on a club | Is that club's 80% band wide in `clubs_on_course`? | Range dispersion that doesn't show on course = you're choosing other clubs; that *does* show on course = real cost. |
| Carry that beats forecast | Does on-course carry match? | Range carries often run 5-15 yd longer than on-course (ideal lies, no wind, full swings). The systematic gap is fine; an *increasing* gap means you're decompensating on-course. |

| When you see this on the course… | …check on the range… | …because |
|---|---|---|
| Approach SG worst in a specific distance bucket | What clubs cover that distance? Where's their dispersion? | The 125-150 yd leak suggests 7i/8i. Range data shows those clubs' real dispersion. |
| Tee-shot SG losing >0.30 with driver | Driver work needed | Get driver onto the GC3 next session — currently the bag has zero measured driver data, so the forecast is loose. |
| Putting trending up over last 10 rounds | Don't over-allocate practice time there | A category that's already improving doesn't need most of your practice — protect the gain, focus elsewhere. |

---

## 6. Data schemas

### 6.1 `rounds_summary.csv` (Arccos)

One row per round. Key columns used in the notebook:

| Column | Type | Meaning |
|---|---|---|
| `round_id` | int | Arccos round identifier |
| `date` | date | Round date (ISO) |
| `course`, `tee_name`, `tee_yards`, `slope`, `rating` | str/int | Course context |
| `holes` | int | 9 or 18 |
| `score`, `par`, `score_to_par` | int | Scoring |
| `putts`, `one_putts`, `three_putts`, `putts_per_gir` | int/float | Putting volume |
| `gir_hits`, `gir_pct`, `fairway_hits`, `fairway_pct` | int/float | Greens, fairways |
| `scramble_chances`, `scramble_saves`, `scramble_pct` | int/float | Short game recovery |
| `sand_chances_native`, `sand_saves_native` | int | From Arccos native flags |
| `penalties` | int | Penalty strokes |
| `avg_drive_yd`, `longest_drive_yd`, `avg_approach_proximity_yd` | float | Driving + approach quality |
| `sg_off_tee_arccos`, `sg_approach_arccos`, `sg_short_arccos`, `sg_putting_arccos`, `sg_total_arccos` | float | **Measured SG vs scratch — the authoritative category numbers.** |
| `sg_off_tee_broadie` … `sg_total_broadie` | float | Independent reconstruction from Broadie tables. Use only for cross-checking. |
| `user_hcp`, `drive_hcp`, `approach_hcp`, `chip_hcp`, `sand_hcp`, `putt_hcp` | float | Arccos's proprietary category handicaps. Note: negative scale, not USGA. |
| `temp_f`, `wind_mph`, `wind_dir`, `weather` | float/str | Weather at tee-off time |

### 6.2 `shots.csv` (Arccos)

One row per shot. Key columns:

| Column | Type | Meaning |
|---|---|---|
| `round_id`, `hole_id`, `shot_num` | int | Which shot in which hole in which round |
| `date` | date | |
| `club`, `club_category` | str | Puller's label per `CLUBTYPE` map. `"Hybrid"` is generic; unknown `clubType` values show as `"Club {N}"` (e.g. `"Club 35"` is your 3-hybrid). Use `arccos.loader.PULLER_CLUBTYPE` + `paired_bag.shots_csv_label` to translate reliably. |
| `shot_distance_yd` | float | **TOTAL distance** the ball travelled (carry + bounce + roll). Not carry. For an iron, ~5-10 yd of this is roll. Don't compare it directly to a launch-monitor carry number. |
| `start_dist_to_pin_yd`, `end_dist_to_pin_yd` | float | Pin distance before/after the shot |
| `start_lat`, `start_lng`, `end_lat`, `end_lng` | float | GPS (only present if `--include-gps`) |
| `start_alt`, `end_alt` | float | Elevation (GPS-dependent) |
| `is_half_swing` | 0/1 | Was this a partial swing? |
| `lie_approx` | str | Approximate lie (tee/fairway/rough/sand/green) |
| `is_tee`, `is_putt` | 0/1 | Tee shot? Putt? |
| `penalties` | int | Penalty strokes on this shot |
| `category_approx` | str | off_tee / approach / short_game / putting |
| `sg_shot_approx` | float | Reconstructed per-shot SG. Directionally accurate; don't read a single shot. |

### 6.3 `holes.csv`, `clubs.csv` (Arccos)

`holes.csv` is one row per hole-round (par, GIR, fairway hit, drive/approach
metrics). `clubs.csv` is per-club aggregate (`smart_distance_yd`,
`normalized_yd`, dispersion). Both useful for deeper drills; not currently
loaded into the four-section notebook.

### 6.4 `outputs/per_club_on_course.csv`

Output of `scripts/forecast_club_distances.py`. One row per club in your **current
paired bag** (retired clubs excluded). Sorted by Smart Distance descending.

| Column | Meaning |
|---|---|
| `Club` | Display label (e.g. "3 Hybrid", "Pitching Wedge"). Uses our overrides for clubTypes the puller doesn't name well. |
| `Make/Model` | E.g. "TaylorMade Qi10", "TaylorMade P770". Helps disambiguate three identically-labelled wedges. |
| `Smart Distance (yd)` | **Authoritative.** Arccos's per-club expected total distance from a well-struck shot. Direct from `_cache_raw/clubs_v6.json`. This is what the Arccos app shows you. Plan club selection around this. |
| `Longest (yd)` | Your longest tracked shot with this club (also from `clubs_v6.json`). Useful as a "what's possible" reference. |
| `Recent p80 (yd)` | 80th percentile of your last-12-month shots with that label. Sanity-check column — should be within a few yards of Smart Distance for normal use. Big gaps suggest the club's profile has changed (regripped, bent, etc.). |
| `n (last 12mo)` | Shot count in the recent window. <5 means the p80 is noisy; lean on Smart Distance instead. The three wedges share a `Wedge` label in shots.csv so they all show the same p80 — Smart Distance per row is the authoritative per-wedge number. |
| `Gap to next (yd)` | Distance gap to the next-shorter club. **<6 = TIGHT** (clubs do the same job). **>18 = WIDE** (hole between them). **Negative = REVERSED** (a "longer" club is actually shorter — usually means the loft order doesn't match the distance order, sign of an overlap or a swing issue). |

### 6.5 GC3 session CSV

One row per shot from the FSX app export. Columns: `Date, Time, Carry, Total,
Peak Height, Offline, Curve, Descent Angle, Hang Time, Ball Speed, Launch Angle,
Launch Direction, Side Spin, Back Spin, Total Spin, Spin Axis Tilt, Club Speed,
Club Speed at Impact, Smash Factor, Angle of Attack, Club Path, Face to Path,
Lie Angle, Dynamic Loft, Closure Rate, Horizontal Impact, Vertical Impact,
Face to Target`. Metadata (golfer, club, date) extracted from the filename
where possible.

---

## 7. Distance metrics: which to use when

Five different distance numbers can appear for the same club. They mean
different things and you'll confuse yourself if you mix them.

| Metric | What it is | When to use |
|---|---|---|
| **Arccos Smart Distance** (`clubs_v6.json`) | Arccos's bias-corrected per-club expected total distance from well-struck shots. Roughly the 80th percentile of recent on-course total distances. | Default for club selection. This is what the Arccos app shows you and the authoritative number. |
| **Recent p80** (computed from `shots.csv`) | 80th percentile of recent on-course shot distances with a given club label. | Sanity-check against Smart Distance. Useful when you want a time-window filter (last 12 months vs all-time). |
| **Median on-course distance** (raw from `shots.csv`) | Middle value of every shot logged with a club. | Almost never — it's dragged down by mis-hits, partial swings, and the like. Don't use for planning. |
| **GC3 carry distance** | Launch-monitor measured carry (no roll). Ideal lie, no wind, full swing. | Range diagnostics, swing-flaw analysis. Don't compare to Arccos numbers without adjusting for roll (≈ −7 yd for irons, −15 yd for woods) and conditions. |
| **GC3 total distance** | GC3 carry + modeled roll. | Comparable to Arccos Smart Distance, with the caveat that GC3 modeled roll uses standard fairway assumptions, not your actual course conditions. |

**Default behaviour of `scripts/forecast_club_distances.py`:** Smart Distance is the
primary column; Recent p80 is shown as a cross-check. The GC3 7-iron is
reported at the bottom for the range-vs-course delta only.

### Current vs Ceiling distances

Two flavours of "what to expect" — used in `outputs/GC3_Launch_Monitor_Cheat_Sheet.xlsx`
and `data/bag_inventory.csv`:

- **Current** = what you actually carry today. From Arccos Smart Distance
  (woods/irons), GC3 measured (7-iron), or your manually-provided wedge
  carries.
- **Ceiling** = realistic best-case with cleaner contact + optimized launch
  and spin, **at your current swing speed**. Per-club delta over Current:
  driver +12, 3W +10, hybrids +9, long irons +8, mid +7, short +6, wedges
  +4 yd. These deltas come from typical observed improvement when amateurs
  dial in smash factor (1.31 → 1.38 area) and launch/spin to spec.

**What Ceiling is NOT.** It is not the target you reach by swinging harder
or by chasing the launch-monitor "perfect" numbers from PGA Tour
references. Anything beyond Ceiling requires actual swing-speed gains —
months of speed-training work, often paired with fitness changes, not a
single range session.

**Why the cheat sheet used to be wrong.** The legacy `scripts/generate_cheat_sheet.py`
used `carry = ball_speed × 2.3 × launch_factor × spin_factor`. The 2.3
coefficient is what Tour pros get on perfectly-optimized shots. Applied to
amateur swing speeds, it produced fantasy distances (driver 280 carry off
an 84 mph swing). The script now ignores that formula for distances and
reads from `data/bag_inventory.csv` directly. The launch/spin/smash target
columns from the legacy formula are kept because those numbers ARE valid
practice targets at any swing speed.

---

## 8. Current diagnostic findings

Snapshot of what the data is telling us as of the most recent sync (50 rounds,
3,012 shots, 2023-08 → 2026-06). Intended as a living section — update as the
picture changes.

### Bag composition

Source of truth: [`data/bag_inventory.csv`](../bag_inventory.csv) at the repo root.
Combines your fitted-bag specs (shaft, loft, lie, swing weight, model year)
with measured / estimated distances. The `in_bag=1` flag is what's currently
carried; `in_bag=0` rows are owned-but-bench (free swaps, no purchase needed).

#### Currently carried (14 clubs)

| Club | Loft | Brand / Model | Shaft | Carry (yd) | Total (yd) | Gap | Swing speed (mph) | Source |
|---|---:|---|---|---:|---:|---:|---:|---|
| Driver | 10.5° | TaylorMade Qi10 Driver | Speeder NX TCS 55g Stiff | 195 | 217 | 19 | 85 | est |
| 3 Wood | 15° | TaylorMade Qi10 Fairway | Speeder NX TCS 55g Stiff | 178 | 198 | 16 | 82 | est |
| 3 Hybrid | 19° | TaylorMade Qi10 Rescue | Speeder NX TCS 59g Stiff | 168 | 182 | 16 | 81 | Arccos |
| 4 Hybrid | 22° | TaylorMade Qi10 Rescue | Speeder NX TCS 59g Stiff | 155 | 166 | 13 | 79 | Arccos |
| 5 Iron | 25.5° | TaylorMade P770 (2022) | Mitsubishi MMT 74g Stiff | 143 | 153 | 12 | 80 | Arccos |
| 6 Iron | 29° | TaylorMade P770 (2022) | Mitsubishi MMT 74g Stiff | 133 | 141 | 12 | 78 | Arccos |
| **7 Iron** | **33°** | TaylorMade P770 (2022) | Mitsubishi MMT 74g Stiff | **127** | 129 | 5 | **74.8** | **GC3 measured** |
| 8 Iron | 37° | TaylorMade P770 (2022) | Mitsubishi MMT 74g Stiff | 120 | 124 | 16 | 72 | Arccos |
| 9 Iron | 41° | TaylorMade P770 (2022) | Mitsubishi MMT 74g Stiff | 105 | 108 | 1 ⚠ | 70 | Arccos |
| PW Iron | 46° | TaylorMade P770 (2022) | Mitsubishi MMT 74g Stiff | 104 | 107 | 24 ⚠ | 68 | Arccos |
| 52° Wedge | 52° (9° bounce) | TaylorMade MG4 | TT DG Tour Issue 115g | 75 | 75 | 17 | 65 | **user** |
| 56° Wedge | 56° (12° bounce) | TaylorMade MG4 | TT DG Tour Issue 115g | 65 | 65 | 10 | 63 | **user** |
| 60° Wedge | 60° (10° bounce) | TaylorMade MG4 | TT DG Tour Issue 115g | 46 | 46 | 19 | 61 | **user** |
| Putter | 3.5° | Scotty Cameron Super Select GOLO 6 | Steel | — | — | — | — | — |

**Source legend:**
- **GC3 measured** = directly observed on Foresight GC3 launch monitor
- **Arccos** = pulled from Arccos Smart Distance (`_cache_raw/clubs_v6.json`)
- **user** = numbers you provided directly (wedges)
- **est** = forecast from the 7i anchor using standard amateur speed-delta + per-club roll model. Confidence drops at the top of the bag (Driver/3W) — get measured driver data on the GC3 to tighten.

**Notes:**
- *Carry* is on-course expected carry on a struck shot; *Total* is Arccos Smart Distance (carry + roll).
- Gap is distance to the next-shorter club in the bag. ⚠ flags: 9i/PW overlap at 1 yd, PW→GW jump of 24 yd.
- Putter row has no distance/speed for the same reason it's irrelevant.

#### Owned, not currently carried (3 clubs)

| Club | Loft | Brand / Model | Loft equivalent to |
|---|---:|---|---|
| 5 Wood | 18° | TaylorMade Qi10 Fairway | 3-Hybrid |
| 7 Wood | 21° | TaylorMade Qi10 Fairway | 4-Hybrid |
| 5 Hybrid | 25° | TaylorMade Qi10 Rescue | 5-Iron (or 9-Wood) |

These three are loft-equivalent to clubs already in the bag, so they're
**free swaps** — try a 5W in place of the 3-Hybrid, or a 5-Hybrid in place
of the 5-Iron, depending on trajectory preference and course conditions.

### Real bag-spacing issues

1. **9-iron ↔ Pitching Wedge overlap.** 108 yd vs 107 yd — same distance,
   PW has more spin/stopping power. Drop the 9-iron candidate.
2. **7-iron ↔ 8-iron tight (4 yd gap).** Looks like a strike issue rather
   than a true overlap — see "Loft adjustments" below for the diagnostic.
3. **Pitching Wedge ↔ GW gap of 24 yd.** Real hole between 107 and 83 yd.
   A 50° wedge is the textbook fix; the user has ruled it out. Lean on
   knockdown PW (~95 yd) and full GW (~83 yd) to cover the gap by feel.

### Strokes-gained picture

| Category | SG/round vs scratch |
|---|---:|
| Off-tee | −3.84 |
| **Approach** | **−5.79** ← biggest leak |
| Short game | −2.45 |
| Putting | −3.10 |
| **Total** | **−15.1** |

**Recent 10 rounds vs all-50:** putting improved +1.5, short game +0.6,
total +2.0. Approach trending slightly worse (−0.2). Putting and short
game don't need most of the practice time — protect the gains, attack
the approach leak.

### Approach SG by distance bucket

The 125-150 yd zone is your single biggest specific leak: **−0.42 SG per
shot across 175 shots in the dataset.** That's roughly 73 strokes given
away over 50 rounds, all from one yardage band — the band you use 7i and
8i for. This dovetails with the GC3 diagnosis: 7i smash 1.31 vs target 1.38,
spin 4924 vs target 6500-7500.

### Loft adjustments — verdict: not recommended

The 7i/8i tightness (4 yd) and 9i/PW overlap (1 yd) look like loft problems
but aren't. Your lofts are essentially **stock P770, ≈1° weak of standard**
across the set — the progression is healthy. The 5i/6i/7i gaps match expected
distance change per degree of loft (~2.5 yd/°); the 8i/9i/PW gaps don't,
because *those clubs* have a contact-quality problem. Bending lofts wouldn't
fix that. Address it with lessons + range work focused on 7i/8i strike, not
with a club fitter.

The only loft change that could be justified is bending the 9-iron 2° stronger
(39°) and the PW 1° weaker (47°) to resolve the 1-yd overlap — but dropping
the 9-iron entirely achieves the same end for $0.

### Practice priorities (in order of stroke ROI)

1. **7i/8i strike improvement** on the GC3. Smash up from 1.31 to 1.35
   buys ~5-7 yd of carry plus tighter dispersion — directly attacks the
   125-150 yd approach leak.
2. **A measured driver session** on the GC3 to anchor the forecast top of bag.
3. **A wedge gapping session** with launch monitor — currently your three
   wedges share one shots.csv label so per-wedge p80 isn't disambiguated.
4. Only after the above: lessons or equipment changes.

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `FileNotFoundError: Arccos store not found at C:\Users\…\golf-data` | First sync never ran, or `GOLF_STORE` is set somewhere unexpected. | Re-run `python setup.py` in `~/tools/golf-reports`. |
| `AttributeError: 'NoneType' object has no attribute 'get'` in `pull_arccos.py` | Upstream bug — `None` hole in your data. | Apply the two-line patch in [§4](#4-arccos-course-workflow) "Known upstream bugs". |
| `~/golf-data/_cache_raw/` exists but no CSVs | Build step skipped or failed. | Run `cd ~/tools/golf-reports/ingest && GOLF_STORE=~/golf-data GOLF_INCLUDE_GPS=1 python pull_arccos.py --build --include-gps`. |
| `scripts/forecast_club_distances.py` errors: "No paired bag found" | `_cache_raw/clubs_v6.json` missing — happens if the puller never finished a fetch phase. | Re-run the puller with both fetch and build (no flags = both). |
| Per-club analysis shows clubs you no longer own (e.g. old 5-wood) | Reading raw `clubs.csv` instead of filtered `paired_bag`. | Use `data.shots_in_bag()` or `data.paired_bag`, not `data.clubs` or unfiltered `data.shots`. |
| `Club 35` appears in shots.csv but not in your bag | Puller's `CLUBTYPE` map doesn't include clubType 35 — your 3-hybrid (Qi10 Rescue 19°) shows as the generic fallback "Club 35". | Already handled by `arccos/loader.py` — it surfaces `paired_bag.label = "3 Hybrid"` for display while keeping `shots_csv_label = "Club 35"` for shots.csv matching. |
| Smart Distance doesn't match the median I see in shots.csv | Different metrics — see [§7](#7-distance-metrics-which-to-use-when). Median is dragged down by mis-hits; Smart Distance is bias-corrected toward struck shots. Use Smart Distance for planning. | Working as intended. |
| 7i shot_distance shows 120 yd but range carry is 127 yd | Different units. Shots.csv is **TOTAL** (carry + roll). Range carry is **CARRY only**. Subtract ~7 yd from Smart Distance to estimate on-course carry. | Working as intended. |
| Cheat sheet shows huge distances (driver 280, 7i 175) | Old cheat sheet (pre-2026-06) used Tour-pro coefficient (2.3 yd/mph). Inflated every distance by 40-80 yd. | Regenerate: `python scripts/generate_cheat_sheet.py` (now reads `data/bag_inventory.csv` for realistic Current carries + adds a Ceiling column). |
| New cheat sheet shows distances different from `outputs/per_club_on_course.csv` | The cheat sheet reads `data/bag_inventory.csv` (manually-curated, includes user-provided wedge carries). `outputs/per_club_on_course.csv` reads Arccos Smart Distance directly. They can diverge if Smart Distance has changed since you last updated the inventory CSV. | Update `data/bag_inventory.csv` from the latest Smart Distance values, then rerun the cheat sheet. |
| 7i / 8i p20 column shows ~30 yd in on-course distances | Chunked/topped shots dragging the distribution tail. | This is real data — don't filter it out. The p80 + 80% band tell the cleaner story. |
| Driver shows -0.30 SG per shot — sounds bad | Per-shot SG below 0 is normal; you're playing par golf, not scratch. -0.30 driver is roughly mid-handicap. | Compare *between* clubs/categories, not against zero. |
| Arccos sync rate-limited error | The puller enforces 600 s between sync runs. | Wait 10 minutes or skip and sync after the next round. |
| Notebook charts blank after re-run | Stale cached output. | Restart kernel, then `Run All`. |
| OneDrive `*-conflicted copy*` files appearing | Git + OneDrive racing on commits. | Pause OneDrive when committing/pushing; delete the conflict copies (the git version wins). |
| `keyring` import errors at Arccos setup | Windows credentials backend not initialized. | The puller falls back to a plaintext `~/.arccos_creds.json` (chmod 600). Re-run setup, accept the fallback prompt. |

---

## 10. Maintenance

### Cadence

| What | When | Command |
|---|---|---|
| New GC3 session | Drop the CSV in the repo root, run the GC3 notebook | (none — notebook auto-discovers) |
| New round played | Sync, regenerate notebook | `python pull_arccos.py --include-gps` then `python scripts/build_notebook.py && jupyter nbconvert --execute --inplace notebooks/Arccos_Course_Analysis.ipynb` |
| New club added to bag | Add row to `data/bag_inventory.csv` (set `in_bag=1`), update `data/Book1.xlsx` for the cheat-sheet swing speed | `python generate_cheat_sheet.py && python forecast_club_distances.py` |
| Bench a club / swap in an Out-of-Bag club | Flip `in_bag` flag in `data/bag_inventory.csv` (don't delete the row — keeps history); re-pair the sensor in the Arccos app | After next Arccos sync, `python scripts/forecast_club_distances.py` to see the new bag-spacing picture |
| Measured driver / wood swing speed | Update the matching row in `data/bag_inventory.csv` (`swing_speed_mph` column) + `data/Book1.xlsx` for the cheat sheet | `python scripts/generate_cheat_sheet.py` |
| Cheat sheet distances look wrong | Check `data/bag_inventory.csv` Current carries are accurate; the cheat sheet is just rendering them. Old cheat sheets (pre-2026-06) used Tour-pro coefficients and were systemically inflated. | `python scripts/generate_cheat_sheet.py` regenerates |

### Backing up

Repo lives at <https://github.com/zachfreitas/golf> (public, MIT). Every commit
pushed via `git push` is the backup.

To restore on a new machine:

```bash
git clone https://github.com/zachfreitas/golf.git
cd golf
pip install -r requirements.txt
# Then follow §4 to install the upstream Arccos puller separately.
```

Raw Arccos data (`~/golf-data/`) is **not** backed up here — it's regenerated
by re-syncing.

### When something gets retired

Move it to `docs/archive/` with a `.md` header explaining why and when. Don't
delete; the project's history is its own diagnostic.

---

## 11. Targeted diagnostics notebook

`notebooks/Arccos_Targeted_Diagnostics.ipynb` (generated from
`scripts/build_diagnostics_notebook.py`) is a focused complement to the broader
`notebooks/Arccos_Course_Analysis.ipynb`. Where the course-analysis notebook answers
"what's happening across my game," this one answers "what specifically
should I do about it."

**Four sections, all backed by helpers in `arccos/diagnostics.py`:**

### §1 — 125-150 yd approach deep-dive

Function: `diagnostics.approach_band_deepdive(data, lo=125, hi=150)`

Slices every approach shot in the band and reports per-shot SG by:
- **Club used** — surfaces which iron/hybrid in this range is leaking most
- **Lie** — quantifies whether rough/tee/fairway is more costly here
- **Wind bucket** — whether wind exacerbates the leak

Current finding (50-round window): 162 shots, −68 SG total. Surprisingly,
**rough is your best lie in this band (−0.28) and tee (par-3s) is worst
(−0.57)**. Suggests the leak isn't approach-from-trouble, it's par-3
tee shots specifically.

### §2 — Putt make-% by distance

Function: `diagnostics.putt_make_by_distance(data)`

First-putt-only (Arccos's phantom 0-distance "putts" are filtered out),
bucketed by feet, with PGA Tour benchmark overlay.

Current finding: you're **at or above Tour from 12 ft+**, but bleeding from
**3-12 ft** (54.5% / 25% / 17% vs Tour 88% / 58% / 33%). The −3.1 SG/round
putting leak is almost entirely short putts; lag distance control is fine.
Practice priority: 5-12 ft straight putts.

### §3 — Lie-penalty matrix

Function: `diagnostics.lie_penalty_matrix(data)`

Per-club Smart Distance broken out by lie (tee / fairway / rough / sand)
from `clubs.csv` terrain columns. **Rough penalty** = fairway distance −
rough distance.

Use this to anchor course-management decisions in numbers: if your driver
loses 15 yd from the rough but you can reach the green from there, vs
3-wood loses 5 yd from the rough — the conservative tee shot may still
let you attack the green.

### §4 — Twin Oaks hole-by-hole

Function: `diagnostics.twin_oaks_hole_heatmap(data, course_name="Twin Oaks GC")`

Per-hole performance at your home course (≥30 rounds in the data), with
**three different "nemesis" lenses**:

- **avg_to_par + avg_rank** — sorted by mean strokes-over-par. Highlights
  holes where occasional blow-ups inflate the average.
- **double_or_worse_pct + double_rank** — % of rounds you make double
  bogey or worse. Often matches the "feels like a nemesis" perception
  much better than the average, because it's not skewed by occasional
  pars dragging the mean down.
- **nemesis_rank** — composite of the two.

Current findings:
- **By avg-strokes-over-par**: holes 1 (+1.58) and 9 (+1.52) lead.
- **By double-bogey-frequency** (the "feels like a nemesis" metric):
  holes 3 and 2 tie at 52% double-or-worse. Hole 3's typical outcome is
  **double bogey** (median +2), not bogey — that's why it feels worse
  than its average suggests.
- Holes 5, 12, 15, 17 are scoring opportunities (lower bogey rate, more
  par-or-better outcomes).

The two-panel chart shows average on top, double-bogey-frequency below.

### §5 — GC3 (range) vs Arccos (course) 7-iron comparison

Function: `diagnostics.range_vs_course_7i(data)` (loads GC3 via
`diagnostics.load_gc3_sessions()`)

Side-by-side distance distributions: GC3 launch-monitor carry vs Arccos
on-course total. Currently 7-iron only because GC3 data is 7-iron only;
adding sessions for other clubs is the path to expanding this.

**Unit caveat critical**: GC3 'Carry' is no-roll; Arccos
`shot_distance_yd` is total (carry + roll). The valid comparison is GC3
carry vs Arccos total minus ~7 yd of typical iron roll. GC3's own 'Total'
column uses a modeled roll that's unrealistically aggressive (60+ yd of
roll on a 7-iron) so it's not used for course comparison.

Second panel shows the GC3 offline distribution — the only lateral-
dispersion signal we have, since course Arccos can't infer aim point.
A non-zero median indicates a swing-path bias.

Current findings:
- GC3 carry median 122 yd, std 29 yd
- Arccos total median 113 yd, std 45 yd (much wider — course conditions add variability)
- Estimated course carry ≈ 106 yd → 16-yard on-course penalty vs range
- GC3 offline median −7 yd (left bias), p20 −19 yd (significant pull misses possible)

### How to re-run

```bash
python scripts/build_diagnostics_notebook.py
jupyter nbconvert --to notebook --execute --inplace notebooks/Arccos_Targeted_Diagnostics.ipynb
```

Or just open the .ipynb in Jupyter and Run All.

### When to add a new section

Add a new analytical function to `arccos/diagnostics.py`, then add a
markdown + code cell pair to `scripts/build_diagnostics_notebook.py`. Regenerate
the notebook and re-execute. The notebook itself is a generated artifact —
never edit it directly.

---

## 12. Scoring Method Level 1 workflow

A separate lens on the Arccos data, framed around the **Will Robins Scoring
Method (Level 1)** rather than strokes gained.

### The idea in one paragraph

Instead of asking "how many strokes did I lose vs scratch in each category?"
(the SG lens), Level 1 splits every hole into two phases: (1) get the ball
inside 100 yd of the pin, then (2) get down in three from there. If you keep
the ball in play AND get down in three on every hole, the arithmetic caps
your worst possible score at bogey — regardless of par. Bogey golf on every
hole is roughly a mid-teens handicap; the promise of L1 is that if you can
execute this simple structure reliably, everything else is upside.

### Metric definitions

Per hole, computed in `arccos/scoring_method.py`:

| Column | Definition |
|---|---|
| `in_play` | No penalty stroke on this hole (`penalties == 0`). |
| `strokes_to_zone` | Number of full-swing shots that **started** outside 100 yd from the pin. (A par-3 shorter than 100 yd starts inside the zone → 0.) |
| `strokes_in_zone` | Total shots minus `strokes_to_zone`. Includes putts. |
| `zone_reached_in_reg` | Reached the zone in the par-or-better target: par 3/4 need ≤1, par 5 needs ≤2. |
| `down_in_3` | `strokes_in_zone` ≤ 3. **This is the headline stat.** |
| `bogey_ceiling_met` | Robins' full promise: `strokes_to_zone ≤ (par − 2)` AND `down_in_3` — meaning this hole's score was at worst bogey. |
| `blow_up` | Double bogey or worse (`score_to_par >= 2`). |

### The counterfactual arithmetic

| Par | To-Zone target | In-Zone target | Bogey ceiling |
|-----|----------------|-----------------|---------------|
| 3   | ≤ 1            | ≤ 3             | 4 |
| 4   | ≤ 2            | ≤ 3             | 5 |
| 5   | ≤ 3            | ≤ 3             | 6 |

`score_if_bogey_ceiling_held()` computes: for each hole in the window, what
would the score have been if you had exactly met the bogey ceiling — par
where it was met, bogey where it wasn't. That's the "if I had played the L1
game perfectly" projection.

### What the notebook produces

`notebooks/Scoring_Method_L1.ipynb` — one parameter (`N` at the top of the
setup cell) controls the lookback window. Sections:

1. **Round selection** — the N most recent rounds by date.
2. **Per-hole metrics** — the raw substrate for everything downstream.
3. **Aggregate dashboard** — headline metrics + par-3/4/5 breakdown.
4. **Practice priorities** — heuristic Robins-lens read from
   `derive_practice_priorities()`. Rules of thumb:
   - `in_play_pct` < 85% → tee-shot decision problem
   - `zone_reg_pct` < 60% → full-swing get-to-zone problem
   - `d3_rate` < 50% → short game / putting problem (sub-split by `putts_per_hole`)
   - `blow_up_pct` > 20% → mindset / recovery problem
5. **The Robins Promise projection** — actual score vs bogey-ceiling
   counterfactual, per round, with bar chart. "Strokes available if you had
   executed L1 on every hole."
6. **Per-round scorecards** — every round in the window, oldest first.
7. **Trend chart** — all four L1 metrics plotted against time.
8. **Excel export** — writes `outputs/scoring_method_L1.xlsx` as a byproduct
   of running the notebook.

### Current read (30-round window: 2024-05-25 to 2026-06-26, 324 holes)

| Metric | Value |
|---|---:|
| In-play % | 88% |
| Zone reached in reg | 34% |
| **Down-in-3 rate** | **69%** |
| Bogey-ceiling met | 61% |
| Blow-ups (dbl+) | 32% |
| Actual vs Robins ceiling | 1643 vs 1419 |

**Where the leak is:**

| Par | Zone-in-reg % | Avg hole len | Interpretation |
|---|---:|---:|---|
| 3 | 95% | 147 yd | Fine — tee shots either start in or near zone |
| 4 | 14% | 324 yd | **Primary leak** |
| 5 | 21% | 473 yd | Secondary leak |

The math on par-4s: with driver Smart Distance 217 yd, an average 324-yd
par-4 leaves 107 yd out after a flushed drive — just outside the 100-yd
zone line. Reaching zone-in-reg on par-4s requires either (a) a driver that
carries with a favorable bounce/roll into the zone or (b) a longer hitter.
At current bag capability, the on-course rule is: **accept the bogey-
ceiling target (2 strokes to zone) on par-4 > 320 yd, and prioritize
in-play over distance.**

The actionable Robins-lens practice/strategy plan is captured in
`tasks/todo.md` under "Scoring Method Level 1 — Zone-in-Reg practice plan."

### How this complements the SG-based diagnostics

| Question | Which lens answers it |
|---|---|
| "Which shot type is bleeding strokes vs scratch?" | SG (`Arccos_Course_Analysis`, §3, §11) |
| "Which specific yardage band on approach?" | SG deep-dive (§11.1) |
| "On any given hole, is my full-swing or short game bleeding?" | Level 1 (this section) |
| "If I execute the L1 game, what's my worst-case score?" | Level 1 (this section) |

Both lenses are simultaneously true. Use SG for range/mechanics prioritization,
use L1 for on-course decision-making and mindset.

### Attribution

The Scoring Method (levels, "gears", scoring zones, down-in-three promise,
purposeful practice framing) is the intellectual work of Will Robins. This
repo implements a derivative analysis inspired by that methodology — none of
Robins' scorecards, workbooks, or proprietary materials are reproduced. If
you want the full methodology, buy his scorecards or program at
[thescoringmethod.com](https://thescoringmethod.com/).

### Re-running

```bash
# Regenerate the notebook from source
python C:/tmp/build_l1_notebook.py

# Execute end-to-end (produces Excel as a side effect)
cd Golf_Analysis
jupyter nbconvert --to notebook --execute --inplace notebooks/Scoring_Method_L1.ipynb
```

Or open the notebook in Jupyter and Run All. To change the lookback window,
edit `LOOKBACK_N` at the top of `C:/tmp/build_l1_notebook.py` (or edit the
`N =` line in the notebook's setup cell and re-run).

### Next levels (not yet implemented)

The Robins methodology also defines Levels 2-4:
- **Level 2** — inside 50 yd, down-in-two goal
- **Level 3** — inside 25 yd, up-and-down conversion
- **Level 4** — on the green, first-putt proximity + three-putt avoidance

Extending `arccos/scoring_method.py` with L2/L3/L4 functions would follow
the same shape — different `ZONE_YARDS` constant, different `DOWN_IN_TARGET`,
different `ZONE_REG_TARGET` map. Tracked in `tasks/todo.md`.
