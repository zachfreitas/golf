# Golf Analysis

Personal golf-improvement workspace combining **range data** (Foresight GC3 launch monitor) and **on-course data** (Arccos shot tracker) to find what to practice and why.

- **Range side (GC3)** → swing mechanics, club gapping, dispersion, smash factor — see `GC3_Golf_Analysis.ipynb`.
- **Course side (Arccos)** → strokes gained by category, course-management decisions, where strokes are being lost under pressure — see `Arccos_Course_Analysis.ipynb`.

## Get started

```bash
git clone https://github.com/zachfreitas/golf.git
cd golf
pip install -r requirements.txt
```

For the Arccos side, install [`chrisdecali/golf-reports`](https://github.com/chrisdecali/golf-reports) separately and run its `setup.py` once to authenticate, then `sync_arccos --include-gps`. Full step-by-step in **[`docs/USER_GUIDE.md`](docs/USER_GUIDE.md)**.

## Documentation

**One comprehensive guide:** [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — covers every file, both workflows (GC3 + Arccos), data schemas, and troubleshooting.

## License

MIT — see [`LICENSE`](LICENSE).
