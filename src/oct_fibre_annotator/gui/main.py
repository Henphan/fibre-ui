from pathlib import Path

from magicgui.widgets import Slider, Container
import napari
import numpy as np
from magicgui import magicgui
from vispy.scene.widgets import widget


def create_app(
    stack_dict: dict[str, np.ndarray],
    output_path: Path = Path("lines.csv"),
) -> napari.Viewer:
    # create_app is a function which takes in the stack dict and the output path
    # it returns the Viewer object from napari
    # NOTE: Does it matter if we return the object or not? We do not even use it.

    # Defining the Viewer, which is the application as far as I know
    viewer = napari.Viewer(title="OCT Fibre Annotator")

    # Add the first stack into the application
    stack_names = list(stack_dict.keys())
    i = 0
    viewer.add_image(
        stack_dict[stack_names[i]],
        name = stack_names[i],
        colormap = "gray",
    )

    # Adding the line drawing layer
    lines_layer = viewer.add_shapes(
        data = [],
        name = "Annotations",
        edge_color = "red",
    )
    lines_layer.mode = "add_line"

    # Callback function for the "Save lines" button
    # Clicking the button will save the coordinates of all lines on the screen
    @magicgui(call_button="Save lines")
    def save_lines() -> None:
        lines = lines_layer.data

        # When no line is drawn
        if len(lines) == 0:
            print("No lines to save.")
            return

        output_path.parent.mkdir(parents=True, exist_ok = True)

        # Write the coordinates of each line down into a .csv
        with open(output_path, "w") as f:
            f.write("start_point, end_point\n")
            for line in lines:
                start, end = line
                f.write("{}, {}\n".format(start, end))

    @magicgui(call_button="Next stack")
    def next_stack() -> None:
        nonlocal i

        viewer.layers.remove(viewer.layers[stack_names[i]]) 

        i += 1

        viewer.add_image(
            stack_dict[stack_names[i]],
            name = stack_names[i],
            colormap = "gray",
        )

        restructure_layers()

    @magicgui(call_button="Previous stack")
    def prev_stack() -> None:
        nonlocal i

        viewer.layers.remove(viewer.layers[stack_names[i]]) 

        i -= 1

        viewer.add_image(
            stack_dict[stack_names[i]],
            name = stack_names[i],
            colormap = "gray",
        )

        restructure_layers()

    def restructure_layers():
        viewer.layers.move(
            viewer.layers.index(lines_layer),
            len(viewer.layers),
        )
        viewer.layers.selection.active = lines_layer
    # Combining the widget into one container
    combined_widget = Container(widgets=[save_lines, next_stack, prev_stack])

    # Create a dock for widgets to the right side
    viewer.window.add_dock_widget(
        widget=combined_widget,
        name="Control panel",
        area="right",
    )

    return viewer


if __name__ == "__main__":
    stack_dict = {
        "Example": np.random.random((20, 256, 256)),
    }

    create_app(stack_dict)
    napari.run()
