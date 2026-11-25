# CLAUDE.md

`oct-fibre-annotator`: a napari desktop app for annotating retinal nerve fibre trajectories in OCT
scans and fitting Jansonius model curves to them. NPSC2001 university project, single developer.

@AGENTS.md

## Commands

```bash
python -m pip install -e . && python -m pip install shapely   # shapely is not in pyproject.toml
python -m oct_fibre_annotator                                 # launch
python3 -m compileall -q src/oct_fibre_annotator              # only verification step
```

No tests, linter, CI or lockfile.

## Environment gotchas

- `main.py` hardcodes `DATA_PATH` and `OUT_PATH` to the developer's machine. Edit them in place to
  run; do not turn them into CLI args or config unless asked. `OUT_PATH` points into `data/`
  (gitignored, as are all `*.csv`).
- `DATA_PATH` must contain only `*_Z<n>.tif.png` slices; any other file (e.g. `.DS_Store`) breaks the
  slice sort in `io/main.py`.
- Jansonius features need system **R** with the **`visualFields`** package (called via rpy2).

## Architecture rules

- Flow: `io.main.create_stack_dict` → `gui.main.create_app` → `napari.run()`, wired in `main.py`.
- Each GUI panel is a factory function holding state in `nonlocal` variables; panels communicate only
  through the callables they return (e.g. `get_stack_name`, `reset_jansonius`). Follow this pattern.
- There is one image layer, named after the current stack key. Navigation and preprocessing remove
  and re-add it, so **always call `restructure_layers()` afterwards**, or the `Annotations` layer
  ends up deselected and buried.
- Preprocessing always rebuilds from the original `stack_dict` array (not cumulative); step order comes
  from the drag-reorderable `pipeline` list and each step is gated by its checkbox.
- Coordinates are napari `(row, col)` everywhere; flip to `(x, y)` only when passing to shapely.
- Jansonius pixel scaling assumes the ONH is ~15° horizontally and ~2° vertically from the fovea.
  These are dataset assumptions, not general constants.
- Annotation CSVs (`<stack>_lines.csv`) have a 7-name header but 8 columns (alpha missing).
  `load_annotations` reads by index and is correct. Fix the header, not the indices.

## Conventions

- `docs/learning.md` is the developer's learning log of things to explain, not documentation.
- Source comments use the same voice: `NOTE:` for questions to self, `TODO:` for cleanups. Match it.
