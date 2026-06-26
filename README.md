# Golf Analysis

Personal golf-improvement workspace combining **range data** (Foresight GC3 launch monitor) and **on-course data** (Arccos shot tracker) to find what to practice and why.

- **Range side (GC3)** → swing mechanics, club gapping, dispersion, smash factor — see `notebooks/GC3_Golf_Analysis.ipynb`.
- **Course side (Arccos)** → strokes gained by category, course-management decisions, where strokes are being lost under pressure — see `notebooks/Arccos_Course_Analysis.ipynb` and the deep-dive `notebooks/Arccos_Targeted_Diagnostics.ipynb`.

## Repo layout

```
Golf_Analysis/
├── arccos/          # Python package: loader + diagnostic helpers
├── data/            # Input source-of-truth — bag_inventory.csv, Book1.xlsx, sessions/
├── outputs/         # Generated artifacts — cheat sheet, per-club CSV, session summaries
├── scripts/         # Standalone scripts + notebook builders
├── notebooks/       # The three .ipynb notebooks
├── docs/            # USER_GUIDE.md + archive/
└── tasks/           # todo.md
```

## Get started

```bash
git clone https://github.com/zachfreitas/golf.git
cd golf
pip install -r requirements.txt

# Run from the repo root — all scripts and notebooks are root-relative.
python scripts/forecast_club_distances.py        # refresh outputs/per_club_on_course.csv
python scripts/generate_cheat_sheet.py           # refresh outputs/GC3_Launch_Monitor_Cheat_Sheet.xlsx
jupyter notebook                                  # then open any notebook in notebooks/
```

For the Arccos side, install [`chrisdecali/golf-reports`](https://github.com/chrisdecali/golf-reports) separately and run its `setup.py` once to authenticate, then sync with `--include-gps`. Full step-by-step in **[`docs/USER_GUIDE.md`](docs/USER_GUIDE.md)**.

## Documentation

**One comprehensive guide:** [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — covers every file, both workflows (GC3 + Arccos), data schemas, distance metrics, troubleshooting.

**Active worklist:** [`tasks/todo.md`](tasks/todo.md).

## License

MIT — see [`LICENSE`](LICENSE).
