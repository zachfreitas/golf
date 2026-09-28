# Lessons Learned

## 2026-07-10 — GC3 Notebook Cell Ordering Bug

**Issue:** `GC3_Golf_Analysis.ipynb` had cells 40–42 (which use the `comparison` variable) placed *before* cell 43 (which defines `comparison` by loading Arccos data and calling `range_vs_course`). Running the notebook caused a `NameError: name 'comparison' is not defined`.

**Fix:** Reordered cells via direct JSON manipulation — moved cells 44 (markdown header) and 43 (data loader) to before cells 40–42. Also stripped stale `execution_count` and `outputs` fields from markdown cells that were causing schema validation warnings on every run.

**How to avoid:** When adding new sections to a notebook that depend on data from another section, always place the data-loading cell *before* any cells that consume it. The "Range vs Course" section header and loader cell were appended at the end but the consuming cells were inserted mid-notebook.
