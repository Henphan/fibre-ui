# Feature specification: ONH and fovea selection on large images

Source: [issue #16, "Bug: cannot plot on fundus images"](https://github.com/Henphan/fibre-ui/issues/16)

## Objective

Since PR #15 the app can load a single image directly from `DATA_PATH`, so fundus photographs can now be
opened alongside OCT stacks. Selecting the ONH or fovea on a fundus image fails, and the Jansonius curve
cannot be calibrated or plotted on that image. The same selection works on the generated sample data.

The bug is not specific to fundus images. Selection fails whenever a landmark is placed at a pixel
coordinate greater than 999, or less than 0. Fundus images are large (the one in `data/sample/` is
1920 × 1920 px), so their ONH and fovea usually fall outside that range. The generated sample images are
256 × 512 px and never do.

This feature makes landmark selection work on images of any size, so the Jansonius tools work on fundus
images as well as on OCT stacks.

## Current behaviour

Reproduced on 2026-11-27 against `main` (`641772b`), napari 0.10.0, magicgui 0.10.2. The Jansonius panel
was driven headlessly (napari `ViewerModel` with `create_layers` and `create_jansonius_panel`, Qt offscreen).
The full `create_app` viewer could not be started offscreen because it needs OpenGL, so the steps below
were not checked by clicking in the live GUI.

**Root cause.** `select_onh` and `select_fovea` in `gui/jansonius_panel.py` declare their coordinate
fields as `{"widget_type": "SpinBox"}` with no bounds, so magicgui uses its default range of **0–999**.
When the user clicks a landmark, `on_onh_change` / `on_fovea_change` copy the point into those SpinBoxes
(`select_onh.onh_x.value = int(x)`). A value outside 0–999 raises:

```text
ValueError: value 1250 is outside of the allowed range: (0, 999)
```

Because the handler sets `waiting = False` and `onh_set = True` (or `fovea_set = True`) **before** the
exception, the app is left in a partly updated state:

| Step after the failed assignment | Result |
|---|---|
| Point added to the `ONH` / `Fovea` layer | Yes, it is drawn where the user clicked |
| SpinBoxes updated | No. They keep their old values (`0, 0` on first use), or only `x` is updated if `x` fits and `y` does not |
| `onh_set` / `fovea_set` | `True` |
| `update_map_button()` | Skipped. The button is enabled later if the other landmark succeeds |
| Active layer / mode | Stays on `ONH` / `Fovea` in `add` mode instead of returning to `Annotations` / `add_line`. Later clicks add extra landmark points |

**Map path** and **Predict psi0** read the SpinBox values, not the layer points. They therefore calibrate
against the stale coordinates and give no warning. Observed results:

| Case | Image | ONH (row, col) | Fovea (row, col) | Outcome |
|---|---|---|---|---|
| Fundus, typical landmark positions | 1920 × 1920 | (960, 1250) | (980, 700) | ONH raises `ValueError`; SpinBox stays `0, 0`. **Map path** is enabled and draws a curve at rows 1419–9935, cols −94–86, off the image |
| Fundus, both landmarks ≤ 999 | 1920 × 1920 | (500, 900) | (520, 400) | Works; curve at rows 529–703, cols 839–967 |
| Generated single image | 256 × 512 | (120, 400) | (130, 200) | Works |
| Generated 3-slice stack | 3 × 256 × 512 | (120, 400) | (130, 200) | Works |
| Click left of the image | 256 × 512 | (120, −10) | (130, 200) | ONH raises `ValueError` for −10, with the same broken state as the fundus case |

The problem existed before PR #15. It only became visible once images wider or taller than 1000 px could
be loaded. Any OCT stack with slices over 1000 px would be affected in the same way.

## Desired behaviour

- Clicking the ONH or fovea anywhere on the image records that point, whatever the image size. The
  SpinBoxes show the clicked pixel coordinates.
- After a landmark is placed, the app returns to the `Annotations` layer in `add_line` mode, as it does
  for small images today.
- **Map path** and **Predict psi0** use the coordinates the user actually selected, so the curve is drawn
  relative to the selected ONH and fovea on fundus images.
- If a landmark cannot be recorded, the app must not mark it as set or enable **Map path** with stale
  coordinates.

## Acceptance criteria

- On the 1920 × 1920 fundus image in `data/sample/`, selecting the ONH at a column or row above 999 records
  the point, updates both SpinBoxes to the clicked coordinates and raises no exception.
- The same holds for the fovea.
- With both landmarks set on the fundus image, **Map path** draws a curve that starts near the selected ONH
  and lies within the image region around the landmarks (not at rows in the thousands beyond the image).
- **Predict psi0** runs on the fundus image with one annotation line and returns three candidates.
- After each landmark selection, `Annotations` is the active layer and its mode is `add_line`.
- Edge cases:
  - Landmarks at the image's last row/column (e.g. 1919) are accepted.
  - The behaviour for a click outside the image (negative or beyond the image size) is decided and
    documented. Either accept the coordinate or reject it without leaving the panel in a half-set state.
  - Images over 1000 px in only one dimension (e.g. 800 × 1500) work.
  - Changing stack still resets the landmarks, curve and predictions (`reset_jansonius()`).
- Existing functionality keeps working. The generated sample stacks and single image behave as in the
  table above: same SpinBox values, same curve.

## Constraints and non-goals

- Limit the change to landmark coordinate handling in `gui/jansonius_panel.py`, unless implementation
  shows another file must change.
- Do not change the Jansonius scaling (`Δcol/15`, `Δrow/2`) or its duplicate in
  `automated_jansonius.generate_jansonius_maps`. Whether those constants suit fundus images is a separate
  question; see [Open questions](#open-questions).
- Do not add input-data validation for `DATA_PATH` (an open `TODO` that stays out of scope).
- Do not change point sizes, colours or other layer styling. Size-7 landmark points are small on a
  1920 px image, but that is a separate issue.
- Do not change how images are loaded. Fundus images keep being read as grayscale.

## Compatibility

- Coordinates stay `(row, col)` in napari layers. The SpinBoxes keep `x` = column and `y` = row, and
  remain editable by hand.
- The panel's factory signature `create_jansonius_panel(viewer, jansonius_map, onh_layer, fovea_layer,
  lines_layer)` and its return value `(jansonius_container, reset_jansonius)` are unchanged.
- The layer names and order (`restructure_layers`) are unchanged.
- The annotation CSV format and `<stack>_lines.csv` naming are unchanged.
- The headless Jansonius check (`python -m oct_fibre_annotator.automated_jansonius`) still ranks `psi0`
  122, 121, 123 first.

## Implementation plan

To be developed collaboratively with the implementation agent.

## Verification

There is no automated test suite. Verification is scripted and manual.

1. **Syntax:** `python -m compileall -q src/oct_fibre_annotator`.
2. **Headless reproduction script:** run the panel-level script used to produce the table in
   [Current behaviour](#current-behaviour), with `QT_QPA_PLATFORM=offscreen`. It builds a `ViewerModel`,
   calls `create_layers` and `create_jansonius_panel`, triggers **Select ONH** / **Select fovea**, adds a
   point to the landmark layer and prints the SpinBox values, the active layer and mode, the **Map path**
   state and the curve's row/column range. It covers the cases in the table plus a landmark at
   (1919, 1919) and an 800 × 1500 image. Expected results: no exceptions for in-image points, SpinBoxes
   equal to the clicked points, `Annotations` / `add_line` active afterwards, and the fundus curve within
   or near the image bounds. The two small-image rows must be unchanged.
3. **Jansonius regression:** `python -m oct_fibre_annotator.automated_jansonius` still gives `psi0`
   122, 121, 123.
4. **Manual GUI acceptance:** set `DATA_PATH` to a folder with the fundus image and a generated stack, then
   launch the app. On the fundus image, select the ONH and the fovea, run **Map path** at a few `psi0`
   values, draw one line and run **Predict psi0**. Check that the curve leaves the ONH and that no error
   appears in the terminal or napari notifications. Switch to the generated stack and check that the
   landmarks reset and that selection, mapping and prediction work as before.

## Open questions

- ~~How should a click outside the image be handled: accept it, clamp it to the image edge, or reject it?~~
  Decided at implementation: accept it as is, within the SpinBox bounds of ±100 000 px (`COORD_LIMIT` in
  `gui/jansonius_panel.py`). That covers every image this app can realistically load (a 100 000 px square
  grayscale image is ~10 GB), so "any size" in this spec means any size up to that bound. A click beyond
  it is rejected: the SpinBox raises, the landmark stays unset and **Map path** stays disabled. The
  landmark layer is still left active in `add` mode in that case, as before.
- The pixel scaling assumes the ONH is ~15° horizontally and ~2° vertically from the fovea, an assumption
  taken from the OCT dataset. Does it hold for fundus images? This needs checking before fundus curves are
  interpreted, but it is out of scope here.
