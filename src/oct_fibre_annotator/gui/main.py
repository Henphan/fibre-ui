from pathlib import Path

from magicgui.widgets import Slider, Container
import napari
import numpy as np
from magicgui import magicgui
from vispy.scene.widgets import widget


def create_app(
    stack_dict: dict[str, np.ndarray],
    output_dir: Path = Path("/home/henphan/GitHub/fibre-ui/data/"),
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
        nonlocal i

        lines = lines_layer.data
        print(lines)

        # When no line is drawn
        if len(lines) == 0:
            print("No lines to save.")
            return

        output_path = output_dir / Path("{}_lines.csv".format(stack_names[i]))
        output_path.parent.mkdir(parents=True, exist_ok = True)

        # Write the coordinates of each line down into an image specific .csv
        with open(output_path, "w") as f:
            f.write("x1,y2,x2,y2\n")
            for line in lines:
                start, end = line
                f.write("{},{},{},{}\n".format(start[0], start[1], end[0], end[1]))

    @magicgui(call_button="Load lines")
    def load_lines() -> None:
        nonlocal i

        output_path = output_dir / Path("{}_lines.csv".format(stack_names[i]))
        # lines = np.loadtxt(output_path, delimiter=',', skiprows=2)
        lines = np.loadtxt(output_path, delimiter=",", skiprows=1).reshape(-1, 2, 2)

        lines_layer.data = []

        for line in lines:
            lines_layer.add(line, shape_type="line")


    @magicgui(call_button="Next stack")
    def next_stack() -> None:
        nonlocal i

        if i + 1 < len(stack_names):
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

        if i - 1 >= 0:
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

    @magicgui(
        threshold = {"widget_type":"FloatSlider", "max":255}
    )
    def threshold_widget(threshold:"float"):
        nonlocal i
        
        name = stack_names[i]
        new_stack = stack_dict[name] > threshold
        viewer.layers.remove(viewer.layers[stack_names[i]]) 

        viewer.add_image(
            new_stack,
            name = name,
            colormap="gray",
        )

        restructure_layers()




    # Combining the widget into one container
    combined_widget = Container(widgets=[save_lines, load_lines, next_stack, prev_stack])

    # Create a dock for widgets to the right side
    viewer.window.add_dock_widget(
        widget=combined_widget,
        name="Control panel",
        area="right",
    )
    viewer.window.add_dock_widget(
        widget=threshold_widget,
        name="Image preprocessing",
        area="right",
        tabify=True,
    )


    return viewer


if __name__ == "__main__":
    stack_dict = {
        "Example": np.random.random((20, 256, 256)),
    }

    create_app(stack_dict)
    napari.run()
