# NPSC2001 | Phase 3 | OCT Fibre Annotator
## A semi-automated approach to determining retinal nerve fibre trajectories in retinal data
This repository contains a Napari application that serves as a platform to aid users in mapping and identifying retinal nerve fibres without the constraints of traditional image processing. This reseearch prototype was developed as part of NPSC2001 research work under the supervision of Dr Andrew Turpin. 
## Current functionality:
- Load and navigate OCT image stacks in a Napari viewer.
- Draw line annotations over the images and save/load them as CSV files.
- Apply Gaussian blur, thresholding and contrast-limited adaptive histogram equalisation (CLAHE) in a user-defined order.
- Select the optic nerve head (ONH) and fovea to calibrate Jansonius curves to image coordinates.
- Display a Jansonius model trajectory for a selected initial angle (`psi0`).
- Compare **one** annotated line with modelled trajectories and display the three candidates with the lowest mean positional error.
## Requirements
- Python **3.12–3.14**, as specified in `pyproject.toml` (tested on 3.12).
- A desktop environment capable of running Napari's Qt interface.
- **R**, installed and on your `PATH`. The app does not start without R: the Jansonius panel imports `rpy2`, which loads R at start-up.
- The R package **`visualFields`**.
- The Python dependencies, which are declared in `pyproject.toml` and installed by `pip` in step 2.
## How do I run the app?
### 1. Install R and `visualFields`
Install R from [CRAN](https://cran.r-project.org/) (or on macOS with Homebrew: `brew install r`). Check that it is on your `PATH`:
```bash
R --version
```
Then install `visualFields`:
```bash
Rscript -e 'install.packages("visualFields", repos = "https://cloud.r-project.org")'
```
### 2. Install the application
From a terminal:
```bash
git clone https://github.com/Henphan/fibre-ui.git
cd fibre-ui

python -m venv .venv
source .venv/bin/activate

python -m pip install -e .
```
To check that `rpy2` can find R, run `python -m rpy2.situation`. If it reports that `R_HOME` is not set (or the app fails with `r_home is None`), set it before running the app:
```bash
export R_HOME=$(R RHOME)
```
With some R installs (for example Homebrew's), start-up prints `Error importing in API mode ... Trying to import in ABI mode`. This is harmless: `rpy2` falls back to ABI mode and the app works normally.
### 3. Configure the data and output paths
The paths are hardcoded. Before running the app, edit these two lines in `src/oct_fibre_annotator/main.py`:
```python
DATA_PATH = Path("/path/to/your/oct_images/")   # folder of OCT images and stacks to load
OUT_PATH = Path("/path/to/fibre-ui/data/")      # where <stack>_lines.csv files are written
```
- `DATA_PATH` must contain **only** images and stack folders in the format described in [Expected input data](#expected-input-data). Any other file breaks loading, and so does an empty folder. On macOS this includes `.DS_Store`, so remove it with `rm /path/to/your/oct_images/.DS_Store` (and from inside each stack folder).
- `OUT_PATH` is created automatically the first time you save lines. `data/` inside the repository is gitignored, so it is a safe choice.
### 4. (Optional) Generate sample data for a smoke test
The OCT dataset is not distributed with this repository. To check that the app starts without it, run the following in the activated environment from the project root. It writes two stacks of three random grayscale slices and one single random image to `data/sample/`:
```bash
python - <<'PY'
from pathlib import Path
import cv2 as cv
import numpy as np

out = Path("data/sample")
rng = np.random.default_rng(0)
for stack in ["DEMO01", "DEMO02"]:
    (out / stack).mkdir(parents=True, exist_ok=True)
    for n in range(1, 4):
        img = rng.integers(0, 256, size=(256, 512), dtype=np.uint8)
        cv.imwrite(str(out / stack / f"{n}.png"), img)
img = rng.integers(0, 256, size=(256, 512), dtype=np.uint8)
cv.imwrite(str(out / "DEMO03.png"), img)
print(sorted(str(p.relative_to(out)) for p in out.rglob("*")))
PY
```
Then set `DATA_PATH` to the absolute path of `data/sample/` in step 3.
### 5. Run
From the project root, with the environment activated:
```bash
python -m oct_fibre_annotator
```
## Expected input data
The loader in `src/oct_fibre_annotator/io/main.py` reads each entry directly inside `DATA_PATH`:
- A **file** is loaded as a single image, named after the filename up to its first dot (`image2.jpg` → `image2`).
- A **folder** is loaded as a stack named after the folder. Its slices must be images named by their number (`1.png`, `2.png`, …) and are ordered by that number. All slices in a stack must be the same size.

For example:
```text
oct_images/
├── image1.png        → image1 (single image)
└── WF01_W_0001/      → WF01_W_0001 (stack of 3 slices)
    ├── 1.png
    ├── 2.png
    └── 3.png
```
Images are read as grayscale. Names must be unique, so `image1.png` and a folder `image1/` cannot coexist, and must not be `ONH`, `Fovea`, `Annotations` or `Jansonius mappings` (the app's other layers). Anything else in `DATA_PATH` or a stack folder (non-image files, nested folders, non-numeric slice names, empty folders) stops the app at start-up.

Older datasets used a flat folder of `<stack>_Z<n>.tif.png` slices. To convert one, move each slice into a folder named after its stack, keeping only the number, e.g. `WF01_W_0001_Z0.tif.png` → `WF01_W_0001/0.tif.png`. The stack keeps its name, so existing `<stack>_lines.csv` annotations still load:
```bash
cd /path/to/your/oct_images
for f in *_Z*.tif.png; do s="${f%_Z*}"; n="${f##*_Z}"; mkdir -p "$s"; mv "$f" "$s/$n"; done
```
## Using the application
1. Launch the app and navigate through the loaded OCT stacks with **Next stack** and **Previous stack** in **Control panel**. Navigate through slices within a stack through the built-in Napari's slider.
2. With the **Annotations** shapes layer selected, draw line segments along candidate nerve fibre trajectories. Choose **Save lines** or **Load lines** to work with per-stack CSV annotations.
3. Open **Image preprocessing** to enable Gaussian blur, thresholding or CLAHE. Drag processing steps to change their order and apply the settings using the widget's action. Each application starts from the original stack, rather than the last processed result.
4. In **Jansonius map**, choose **Select ONH** and click its location in the viewer; repeat with **Select fovea**. Landmark coordinates are accepted from −100 000 to 100 000 px, so large images such as fundus photographs work and a click just outside the image is recorded as is. Specify the radius bounds and `psi0`, then select **Map path** to visualise a curve.
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

1. **Dependency management:** version-lock a tested Python–R environment and verify a clean install on another machine.
2. **Portability:** remove hardcoded paths from `main.py` in favour of configuration, environment variables or a file chooser.
3. **Prediction model:** The current scoring uses the average distance between sampled points on one straight annotation and each candidate Jansonius curve. It does not use line direction, model confidence or multiple annotations. Validate the anatomical mapping and scaling assumptions before interpreting the ranked candidates.
