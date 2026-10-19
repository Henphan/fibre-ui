# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`oct-fibre-annotator` — a napari desktop app for annotating and predicting retinal nerve fibre
trajectories in OCT scans. University project (NPSC2001), single developer, early stage.

## Commands

```bash
uv sync                          # install deps into .venv (uv-managed, editable install of src/)
uv run python -m oct_fibre_annotator   # launch the app
```

There is no test suite (`tests/` is empty), no linter, and no CI. The only verification step used so
far is a syntax check:

```bash
python3 -m py_compile src/oct_fibre_annotator/gui/main.py src/oct_fibre_annotator/io/main.py src/oct_fibre_annotator/main.py
```

## Environment gotchas

- **`main.py` contains hardcoded absolute paths** (`DATA_PATH`, `OUT_PATH`) pointing at the
  developer's machine. Anything that runs the app must edit these first. They are edited in-place
  rather than parameterised — do not "fix" this into CLI args unless asked.
- **`rpy2` is imported by `gui/main.py` but is not in `pyproject.toml` or `uv.lock`.** It is only
  present in the existing `.venv`. A fresh `uv sync` will produce an app that crashes when the
  Jansonius widget is used. The Jansonius feature also needs a system **R** install with the
  **`visualFields`** R package.
- The venv runs Python 3.14 even though `requires-python` is `>=3.12, <3.15`.

## Architecture

Three-stage flow, all wired in `main.py`:

```
io.main.create_stack_dict(DATA_PATH)  ->  stack_dict  ->  gui.main.create_app(stack_dict, OUT_PATH)  ->  napari.run()
```

- **`io/main.py`** — reads a flat directory of OCT slices named `WF**_W_****_Z<n>.tif.png`. The key
  for a stack is everything before `_Z`; slices are sorted by the integer after `_Z` and stacked
  into a `(n_slices, height, width)` grayscale `np.ndarray`. Returns `dict[str, np.ndarray]`.
- **`gui/main.py`** — the whole UI, built as closures inside `create_app` sharing a `nonlocal i`
  index into `stack_names`. Everything is a `magicgui` widget docked to the right of the viewer.
- **`models/`, `processing/`** — empty placeholder packages for future work.

### napari layer conventions

There is exactly one image layer at a time, **named after the current stack key**, plus a persistent
`Annotations` shapes layer in `add_line` mode. Stack navigation and preprocessing both work by
*removing and re-adding* the image layer, so any such operation must be followed by
`restructure_layers()`, which moves `Annotations` back to the top and re-selects it. Forgetting this
leaves the user drawing into nothing.

Preprocessing (`preprocessing_widgets`) always rebuilds from the *original* `stack_dict` array — it
is not cumulative. The order of operations comes from the drag-reorderable `QListWidget` named
`pipeline`, and each step is additionally gated by its own checkbox (`use_blur`, `use_threshold`,
`use_clahe`).

### Annotation CSV format

`save_lines`/`load_lines` write `{stack_name}_lines.csv` into `OUT_PATH`. Note the header row says
`r,g,b,y1,x1,y2,x2` (7 names) but **8 columns are written** — the alpha channel is missing from the
header. `load_lines` reads by column index (`[:, :4]` = RGBA, `[:, 4:8]` = coords), so it round-trips
correctly; the header is just wrong. Fix the header, not the indices, if this is ever cleaned up.

Coordinates are napari-native `(row, col)` i.e. `(y, x)`.

### Jansonius mapping

`jansonius_widget` calls the R `visualFields` package via rpy2: `bundlePath(psi0)` gives psi as a
function of radius, sampled over the `[min, max]` degree range from the paired `jansonius_range`
spinboxes, then `jpolar2cart` converts to Cartesian degrees. Those degrees are mapped to pixels with
constants baked into the function:

```
fovea = (row 192, col 384);  x_scale = 237/15 px/deg;  y_scale = 22/2 px/deg
rows = fovea_row - y_scale * y      # note the sign flip: image rows grow downward
cols = fovea_col + x_scale * x
```

These constants are specific to the current dataset's scan geometry. Each call adds a *new*
`Jansonius mappings` points layer rather than updating the existing one.

## Repo conventions

- `data/` and all `*.csv` are gitignored; `data/` currently holds committed-before-ignore sample
  annotation output, and `lines.csv`/`points.csv` at the root are older scratch exports with a
  different (non-loadable) format.
- `docs/learning.md` is the developer's running list of things they want explained — it is a
  learning log, not documentation. Comments in the source are written in the same voice (`NOTE:`
  questions to self, `TODO:` cleanups). Match that register when editing existing code.
