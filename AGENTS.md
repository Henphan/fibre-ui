# AGENTS.md

`oct-fibre-annotator`: a napari desktop app for annotating retinal nerve fibre trajectories in OCT
scans and fitting Jansonius model curves to them. NPSC2001 research prototype, single developer.
`README.md` covers user setup, input data layout and the CSV format; this file covers what an agent
needs on top of it. Items marked *(assumption)* can't be checked from the code.

## Scope of changes

- Do not implement extra features unless explicitly requested by the user.
- Keep changes minimal and limited to the requested task.
- When refactoring, mirror the original implementation and preserve its behaviour. Do not add
  validation, error handling, bug fixes, or unrelated cleanup unless explicitly requested.
- If you notice an issue outside the requested scope, mention it rather than changing it.

## Setup and launch

- Follow [README setup](README.md#how-do-i-run-the-app) to install and launch the app. Step 4 generates sample
  data in `data/sample/`.
- The app requires system **R** at startup because `gui/jansonius_panel.py` imports rpy2 at module
  load. Jansonius mapping and prediction load the **`visualFields`** package when invoked.
- `DATA_PATH` and `OUT_PATH` are hardcoded in `main.py`. Set them locally as needed for smoke tests
  and keep machine-specific path edits out of the submitted diff. Keep the hardcoded configuration
  unless asked to change it.

## Verification

There are no tests, linter, CI or lockfile.

- For Python changes, run `python -m compileall -q src/oct_fibre_annotator` to check syntax.
- For Jansonius changes, run `python -m oct_fibre_annotator.automated_jansonius` with R and
  `visualFields`. Compare the printed ranking with the bundled example's expected top three
  `psi0` values (122, 121, 123 in order).
- For GUI changes, launch the app and exercise the affected interaction when the environment
  allows. Report any verification you could not run.

## Architecture

- Flow: `io.main.create_stack_dict(DATA_PATH)` → `gui.main.create_app(stack_dict, OUT_PATH)` →
  `napari.run()`, wired in `main.py`.
- `io/` handles loading and annotation CSVs. `processing/` uses NumPy and OpenCV without GUI
  dependencies. `gui/` holds the panels and `layers.py`. `automated_jansonius.py` generates and
  scores candidate curves. `models/` is an empty placeholder.
- Panels are factory functions that receive shared layer objects and callbacks. They use
  `nonlocal` variables where callbacks need shared panel state. Follow this pattern. Construct
  the Jansonius panel before navigation in `gui/main.py` because navigation needs `reset_jansonius`.

## Invariants

- **Layers:** one image layer named after the current stack key, plus four fixed layers:
  `Jansonius mappings`, `ONH`, `Fovea`, `Annotations`. Layers are looked up by name, and
  `create_app` rejects stack names that clash with the fixed ones. Extend that check if you add a
  layer.
- Navigation and preprocessing remove and re-add the image layer. **Always call
  `restructure_layers()` afterwards**, or `Annotations` ends up deselected and buried.
- Changing stack calls `reset_jansonius()`, which clears the landmarks, the curve and the
  predictions. It does not clear annotation lines.
- Preprocessing always rebuilds from the original `stack_dict` array; it is not cumulative. Step
  order comes from the drag-reorderable `QListWidget`, and its item text is matched by exact string
  in `preprocess_stack` (`"Gaussian blur"`, `"Threshold"`, `"CLAHE"`). Rename both together.
- Store napari and annotation coordinates as `(row, col)`. Jansonius calculations convert
  Cartesian `(x, y)` to image coordinates. Shapely receives `(col, row)`.
- Jansonius pixel scaling (`Δcol/15`, `Δrow/2` from the fovea) is duplicated in
  `jansonius_panel.jansonius_widget` and `automated_jansonius.generate_jansonius_maps`. Keep the two
  in sync. *(assumption)* 15 and 2 reflect the ONH sitting ~15° horizontally and ~2° vertically from
  the fovea in this dataset; they are not general constants.
- Any `DATA_PATH` entry that isn't an image or a folder of numbered slices (e.g. `.DS_Store`, an
  empty folder) raises at start-up. Validation is an open `TODO`; don't add it unless asked.
  `create_keys` in `io/main.py` is unused, left over from the old `_Z` flat layout.
- Known issues in annotation CSVs (`<stack>_lines.csv`) include a missing `a` header and a
  single-row load failure. `load_annotations` reads columns by position, so preserve their
  order when changing the header.

## Compatibility

- Python 3.12–3.14 per `pyproject.toml`; only 3.12 has been tested. Dependencies are unpinned.
- With Homebrew R, rpy2 prints `Error importing in API mode … Trying to import in ABI mode`. This is
  harmless. If rpy2 can't find R, set `export R_HOME=$(R RHOME)`.
- Besides `main.py`, `create_app` has a hardcoded default `output_dir` (a Linux path). It isn't used
  because `main.py` always passes `OUT_PATH`.

## Conventions

- Source comments use the developer's voice: `NOTE:` for questions to self, `TODO:` for cleanups,
  and plain `#` comments above functions describing inputs and returns. Match the surrounding file.
- The `if __name__ == "__main__":` blocks in `gui/main.py` and `automated_jansonius.py` are developer
  scratch. Leave them alone (the second one is the headless check above).
- `docs/learning.md` is the developer's learning log of things to explain, not documentation. Don't
  edit it unless asked.
- When changing user-facing behaviour, the input layout or the CSV format, update `README.md` too.
- Work happens on `feature/*` branches merged into `main` by PR.
