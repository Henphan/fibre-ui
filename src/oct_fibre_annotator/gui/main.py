from pathlib import Path

import napari
import numpy as np

from oct_fibre_annotator.gui.control_panel import create_control_panel
from oct_fibre_annotator.gui.jansonius_panel import create_jansonius_panel
from oct_fibre_annotator.gui.layers import create_layers
from oct_fibre_annotator.gui.navigation import create_navigation
from oct_fibre_annotator.gui.preprocessing_panel import create_preprocessing_panel

def create_app(
    stack_dict: dict[str, np.ndarray],
    output_dir: Path = Path("/home/henphan/GitHub/fibre-ui/data/"),
) -> napari.Viewer:
    # create_app is a function which takes in the stack dict and the output path
        # stack dict: dictionary where the key is the stack name and the value is the array of images
        # output path: where the csv containing the line coordinates are written to
    # Returns the Viewer object from napari
    # NOTE: Does it matter if we return the object or not? We do not even use it.

    # Defining the Viewer, which is the application as far as I know
    viewer = napari.Viewer(title="OCT Fibre Annotator")

    # Add the first stack of OCT scans into the application as a layer
    stack_names = list(stack_dict.keys())
    jansonius_map, onh_layer, fovea_layer, lines_layer = create_layers(
        viewer, stack_dict[stack_names[0]], stack_names[0]
    )

    jansonius_container, reset_jansonius = create_jansonius_panel(
        viewer, jansonius_map, onh_layer, fovea_layer, lines_layer,
    )
    next_stack, prev_stack, get_stack_name = create_navigation(
        viewer, stack_dict, stack_names, jansonius_map, onh_layer, fovea_layer,
        lines_layer, reset_jansonius,
    )
    io_container = create_control_panel(
        lines_layer, output_dir, get_stack_name, next_stack, prev_stack,
    )
    preprocessing_container = create_preprocessing_panel(
        viewer, stack_dict, get_stack_name, jansonius_map, onh_layer, fovea_layer, lines_layer,
    )

    # Create a dock for widgets to the right side
    viewer.window.add_dock_widget(
        widget=io_container,
        name="Control panel",
        area="right",
    )
    viewer.window.add_dock_widget(
        widget = jansonius_container,
        name = "Jansonius map",
        area = "right",
        tabify=True,
    )

    viewer.window.add_dock_widget(
        widget=preprocessing_container,
        name="Image preprocessing",
        area="right",
        tabify=True,
    )

    return viewer


if __name__ == "__main__":
    # stack_dict = {
    #     "Example": np.random.random((20, 256, 256)),
    # }
    #
    # create_app(stack_dict)
    # napari.run()

    from rpy2.robjects.packages import importr
    from rpy2.robjects import FloatVector, DataFrame

    vf = importr("visualFields")

    path = vf.bundlePath(-125)

    r = FloatVector(range(4,20))
    psi = path(r)

    rpsi = DataFrame({
        "r":r,
        "psi":psi,
    })

    coords = vf.jpolar2cart(rpsi)

    x = np.asarray(coords.rx2("x"))
    y = np.asarray(coords.rx2("y"))

    coordinates = np.column_stack((x, y))

    new_coord = lambda x, y: (384+(237/15)*x, 192+(22/2)*y)





