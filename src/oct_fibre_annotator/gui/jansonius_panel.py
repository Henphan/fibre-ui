import numpy as np
from magicgui import magicgui
from magicgui.widgets import Container, FloatSpinBox
from rpy2.robjects.packages import importr
from rpy2.robjects import FloatVector, DataFrame

from oct_fibre_annotator.automated_jansonius import (
    generate_jansonius_maps,
    positional_error,
)
from oct_fibre_annotator.gui.layers import restructure_layers


def create_jansonius_panel(viewer, jansonius_map, onh_layer, fovea_layer, lines_layer):
    # Buttons for the jansonius mapping
    # FloatSpinBox for the angle of incidence

    @magicgui(
        call_button = "Map path",
        psi0 = {
            "widget_type": "FloatSpinBox",
            "min": -180.0,
            "max": 180.0,
            "step": 0.1,
        },
    )
    def jansonius_widget(
        psi0: float,
    ):
        vf = importr("visualFields")

        path = vf.bundlePath(psi0)

        lower = jansonius_range[0].value
        upper = jansonius_range[1].value

        # Boundary checking for the inputs
        if np.abs(lower-upper) < 0.1:
            raise ValueError("Invalid values")
        if upper < lower:
            raise ValueError("Invalid values")

        #NOTE: The step of the mapping is set here
        r = FloatVector(np.arange(lower, upper, 0.1))
        psi = path(r)

        rpsi = DataFrame({
            "r":r,
            "psi":psi,
        })

        coords = vf.jpolar2cart(rpsi)

        # converting the coords to match the OCT scan
        x = np.asarray(coords.rx2("x"))
        y = np.asarray(coords.rx2("y"))

        # calculating the scales using selected fovea and onh
        x_scale = (select_onh.onh_x.value - select_fovea.fovea_x.value) / 15
        y_scale = (select_onh.onh_y.value - select_fovea.fovea_y.value) / 2

        # calculating the scaled coordinates
        cols = x_scale * x + select_fovea.fovea_x.value
        rows = y_scale * y + select_fovea.fovea_y.value

        scaled_coords = np.column_stack((rows, cols))

        jansonius_map.data = scaled_coords

        restructure_layers(viewer, jansonius_map, onh_layer, fovea_layer, lines_layer)

    # Disabling the "map path" button initially
    jansonius_widget.call_button.enabled = False

    # Buttons for selecting the features on the OCT scan
    # waiting is a bool value which determines whether the app is waiting for an event from the user
    waiting = False

    @magicgui(
        call_button = "Select ONH",
        onh_x = {"widget_type": "SpinBox"},
        onh_y = {"widget_type": "SpinBox"},
    )
    def select_onh(onh_x:int, onh_y:int):
        nonlocal waiting

        # Clear the point and then wait for user's input
        # Order matters a lot due to event being monitored
        onh_layer.data = np.empty((0, 2))
        waiting = True
        viewer.layers.selection.active = onh_layer
        onh_layer.mode = "add"


    @magicgui(
        call_button="Select fovea",
        fovea_x={"widget_type": "SpinBox"},
        fovea_y={"widget_type": "SpinBox"},
    )
    def select_fovea(fovea_x: int, fovea_y: int):
        nonlocal waiting

        # Clear the point and then wait for user's input
        # Order matters a lot due to event being monitored
        fovea_layer.data = np.empty((0, 2))
        waiting = True
        viewer.layers.selection.active = fovea_layer
        fovea_layer.mode = "add"

    # Declaring initial values for fovea_set and onh_set for the button blocking
    fovea_set = False
    onh_set = False

    #NOTE: NEW CODE
    @magicgui(call_button="Predict psi0")
    def predict_psi0():
        # Require calibration
        if not fovea_set or not onh_set:
            #NOTE: PLACEHOLDER ERROR
            print("Select the fovea and ONH first.")
            return

        # Only support one annotation for now
        if len(lines_layer.data) != 1:
            #NOTE: PLACEHOLDER ERROR
            print("Exactly one annotation must be drawn.")
            return

        # Extract annotation
        annotation = lines_layer.data[0]

        # Coordinates are stored as (row, col)
        fovea = (
            select_fovea.fovea_y.value,
            select_fovea.fovea_x.value,
        )

        onh = (
            select_onh.onh_y.value,
            select_onh.onh_x.value,
        )

        # Generate candidate mappings
        mappings = generate_jansonius_maps(
            fovea=fovea,
            onh=onh,
        )

        # Calculate positional error for every psi0
        errors = {}

        for psi0, curve in mappings.items():
            errors[psi0] = positional_error(
                annotation=annotation,
                jansonius_curve=curve,
            )

        # Find three lowest-error candidates
        candidates = sorted(
            errors.items(),
            key=lambda item: item[1],
        )[:3]

        print("Top psi0 candidates:")

        for psi0, error in candidates:
            print(f"psi0: {psi0}, positional error: {error:.2f}")   

    def on_onh_change(event):
        nonlocal waiting, onh_set

        if waiting and len(onh_layer.data) == 1:
            waiting = False
            onh_set = True

            # changing the values of the SpinBoxes
            y,x = onh_layer.data[0]
            select_onh.onh_x.value = int(x)
            select_onh.onh_y.value = int(y)

            update_map_button()

            viewer.layers.selection.active = lines_layer
            lines_layer.mode = "add_line"

    def on_fovea_change(event):
        nonlocal waiting, fovea_set

        if waiting and len(fovea_layer.data) == 1:
            waiting = False
            fovea_set = True

            # changing the values of the SpinBoxes
            y,x = fovea_layer.data[0]
            select_fovea.fovea_x.value = int(x)
            select_fovea.fovea_y.value = int(y)

            update_map_button()

            viewer.layers.selection.active = lines_layer
            lines_layer.mode = "add_line"

    def update_map_button():
        jansonius_widget.call_button.enabled = fovea_set and onh_set



    # whenever fovea_layer/onh_layer .data changes, run on_fovea_change()
    fovea_layer.events.data.connect(on_fovea_change)
    onh_layer.events.data.connect(on_onh_change)

    # Combining the radius widgets for the jansonius mapping
    # FloatSpinBox is used because we are taking the range between the values by steps of 0.1 anyways
    jansonius_range = Container(
        widgets=[
            FloatSpinBox(value=4, min=4, max=40, label="Min"),
            FloatSpinBox(value=20, min=4, max=40, label="Max"),
        ],
        layout="horizontal",
    )
    # jansonius_widget.insert(1, jansonius_range)
    # Combingin widgets for the jansoinus tab
    jansonius_container = Container(
        widgets = [
            select_onh,
            select_fovea,
            jansonius_range,
            jansonius_widget,
            predict_psi0,
        ],
        labels = False
    )

    def reset_jansonius():
        nonlocal onh_set, fovea_set
        onh_set = False
        fovea_set = False
        fovea_layer.data = np.empty((0, 2))
        onh_layer.data = np.empty((0, 2))
        jansonius_map.data = []
        update_map_button()

    return jansonius_container, reset_jansonius
