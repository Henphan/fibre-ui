# NPSC2001 | Phase 3 | OCT Fibre Annotator
## A semi-automated approach to determining retinal nerve fibre trajectories in retinal data
This repository contains a Napari application that serves as a platform to aid users in mapping and identifying retinal nerve fibres without the temporal constraints of traditional image processing.
## Current functionality:
- Load and navigate OCT image stacks in a Napari viewer.
- Draw line annotations over the images and save/load them as CSV files.
- Apply Gaussian blur, thresholding and contrast-limited adaptive histogram equalisation (CLAHE) in a user-defined order.
- Select the optic nerve head (ONH) and fovea to calibrate Jansonius curves to image coordinates.
- Display a Jansonius model trajectory for a selected initial angle (`psi0`).
- Compare **one** annotated line with modelled trajectories and display the three candidates with the lowest mean positional error.
## Requirements and installation
- Python **3.12–3.14**, as specified in `pyproject.toml`.
- A desktop environment capable of running Napari's Qt interface.
- Python dependencies declared in `pyproject.toml`: `numpy`, `napari[pyqt6]`, `opencv-python`, `pandas` and `rpy2`.
- **Shapely**, also required by `automated_jansonius.py` but not yet declared in `pyproject.toml`.
- A working **R installation** with the R package **`visualFields`** available to `rpy2`.
## How do I run the app?
From a terminal:
```bash
git clone https://github.com/Henphan/fibre-ui.git
cd fibre-ui

python -m venv .venv
source .venv/bin/activate

python -m pip install -e .
python -m pip install shapely
```
In R, install the required package if it is not already available:

```r
install.packages("visualFields")
```
Run from the project root:
```
python -m oct_fibre_annotator
```
## Expected input data
With the current implementation, the loader in `src/oct_fibre_annotator/io/main.py` expects a **very specific** data format. Specifically, a flat directory of grayscale-readable OCT slices with filenames containing `_Z` followed by an integer slice index, for example:
```text
WF01_W_0001_Z0.tif.png
WF01_W_0001_Z1.tif.png
WF01_W_0001_Z2.tif.png
```
## Using the application
1. Launch the app and navigate through the loaded OCT stacks with **Next stack** and **Previous stack** in **Control panel**. Navigate through slices within a stack through the built-in Napari's slider.
2. With the **Annotations** shapes layer selected, draw line segments along candidate nerve fibre trajectories. Choose **Save lines** or **Load lines** to work with per-stack CSV annotations.
3. Open **Image preprocessing** to enable Gaussian blur, thresholding or CLAHE. Drag processing steps to change their order and apply the settings using the widget's action. Each application starts from the original stack, rather than the last processed result.
4. In **Jansonius map**, choose **Select ONH** and click its location in the viewer; repeat with **Select fovea**. Specify the radius bounds and `psi0`, then select **Map path** to visualise a curve.
5. To try **Predict psi0**, ensure both landmarks are selected and exactly **one** annotation line is present. The widget generates candidate curves for integer angles from `-180` through `179` and displays the three lowest positional-error scores.
## Repository layout

```text
src/oct_fibre_annotator/
├── __main__.py              # Python module entry point
├── main.py                  # Dataset/output paths and application start-up
├── automated_jansonius.py  # Candidate trajectory generation and error scoring
├── gui/
│   ├── main.py              # Napari viewer and dock layout
│   ├── layers.py            # Image, point and annotation layers
│   ├── navigation.py        # Stack navigation
│   ├── control_panel.py     # Annotation save/load controls
│   ├── preprocessing_panel.py # Preprocessing controls and pipeline order
│   └── jansonius_panel.py   # Landmark selection, mapping and prediction UI
├── io/
│   ├── main.py              # Load and group OCT slices
│   └── annotations.py       # CSV annotation serialisation
├── processing/
│   └── preprocessing.py     # OpenCV image transformations
└── models/                  # Placeholder for future model-related code
```

### Data flow

`main.py` loads files into a dictionary of image stacks (`create_stack_dict`), passes it to the Napari interface (`create_app`) and starts the event loop (`napari.run`). GUI modules maintain interactive layers, process images and write line annotations. Jansonius calculations call the R `visualFields` package through `rpy2`.

**Coordinate convention:** Napari line and point data use `(row, column)` = `(y, x)` coordinates. Geometry passed into Shapely is converted to `(x, y)`.
## Annotation output

The **Save lines** action writes files named `<stack_name>_lines.csv` to `OUT_PATH`, with RGBA edge colour and two endpoints per annotation. The current writer emits **eight data values** (`r,g,b,a,y1,x1,y2,x2`) but its header contains only **seven names** (`r,g,b,y1,x1,y2,x2`). This inconsistency should be corrected before using the CSV format with other software. The loader indexes eight columns and may also fail for a file containing only one data row because `numpy.loadtxt` returns a one-dimensional array in that case.
## Known limitations and handover priorities

1. **Dependency management:** add `shapely` to `pyproject.toml`, document/version-lock a tested Python–R environment and verify a clean install on another machine.
2. **Portability:** remove hardcoded paths from `main.py` in favour of configuration, environment variables or a file chooser.
3. **Prediction model:** The current scoring uses the average distance between sampled points on one straight annotation and each candidate Jansonius curve. It does not use line direction, model confidence or multiple annotations. Validate the anatomical mapping and scaling assumptions before interpreting the ranked candidates.
