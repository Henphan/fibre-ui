from pathlib import Path

from magicgui.widgets import Slider
import napari
import numpy as np
from magicgui import magicgui


def create_app(
    stack_dict: dict[str, np.ndarray],
    output_path: Path = Path("lines.csv"),
) -> napari.Viewer:
    viewer = napari.Viewer(title="OCT Fibre Annotator")

    for name, stack in stack_dict.items():
        viewer.add_image(
            stack,
            name=name,
            colormap="gray",
        )

    lines_layer = viewer.add_shapes(
        data = [],
        name = "Annotations",
        edge_color = "red",
    )

    @magicgui(call_button="Save points")
    def save_points() -> None:
        lines = lines_layer.data

        if len(lines) == 0:
            print("No lines to save.")
            return

        output_path.parent.mkdir(parents=True, exist_ok = True)


        with open(output_path, "w") as f:
            f.write("start_point, end_point\n")
            for line in lines:
                start, end = line
                f.write("{}, {}\n".format(start, end))

    viewer.window.add_dock_widget(
        save_points,
        name="Point Controls",
        area="right",
    )

    return viewer


if __name__ == "__main__":
    stack_dict = {
        "Example": np.random.random((20, 256, 256)),
    }

    create_app(stack_dict)
    napari.run()
