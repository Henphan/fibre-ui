from pathlib import Path

import napari
import numpy as np
from magicgui import magicgui


def create_app(
    stack_dict: dict[str, np.ndarray],
    output_path: Path = Path("points.csv"),
) -> napari.Viewer:
    viewer = napari.Viewer(title="OCT Fibre Annotator")

    for name, stack in stack_dict.items():
        viewer.add_image(
            stack,
            name=name,
            colormap="gray",
        )

    points_layer = viewer.add_points(
        data=[],
        name="Annotations",
        face_color="red",
        size=3,
    )
    points_layer.mode = "add"

    @magicgui(call_button="Save points")
    def save_points() -> None:
        points = points_layer.data

        if len(points) == 0:
            print("No points to save.")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(
            output_path,
            points,
            delimiter=",",
            header="y,x",
            comments="",
        )

        print(f"Saved {len(points)} points to {output_path}")

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
