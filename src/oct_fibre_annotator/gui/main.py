from pathlib import Path

from magicgui.widgets import Slider, Container, Label, CheckBox, SpinBox
import napari
import numpy as np
import cv2 as cv
from magicgui import magicgui
from vispy.scene.widgets import widget
from qtpy.QtWidgets import QListWidget, QAbstractItemView

from rpy2.robjects.packages import importr
from rpy2.robjects import FloatVector, DataFrame

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
        colours = lines_layer.edge_color

        # When no line is drawn
        if len(lines) == 0:
            print("No lines to save.")
            return

        output_path = output_dir / Path("{}_lines.csv".format(stack_names[i]))
        output_path.parent.mkdir(parents=True, exist_ok = True)

        # Write the coordinates of each line down into an image specific .csv
        with open(output_path, "w") as f:
            f.write("r,g,b,y1,x1,y2,x2\n")
            # NOTE: what is zip?
            for line, colour in zip(lines, colours):
                start, end = line
                r,g,b,a = colour
                f.write("{},{},{},{},{},{},{},{}\n".format(r,g,b,a,start[0], start[1], end[0], end[1]))

    @magicgui(call_button="Load lines")
    def load_lines() -> None:
        nonlocal i

        output_path = output_dir / Path("{}_lines.csv".format(stack_names[i]))
        data = np.loadtxt(output_path, delimiter=",", skiprows=1)
        lines = data[:,4:8].reshape(-1,2,2)
        colours = data[:,:4]

        lines_layer.data = []

        for line in lines:
            lines_layer.add(line, shape_type="line")
        lines_layer.edge_color = colours


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
        threshold = {
            "widget_type":"Slider",
            "max":255,
        },
        blur = {
            "widget_type": "SpinBox",
            "min": 1,
            "max": 51,
            "step": 2,
        },
    )
    def preprocessing_widgets(
        threshold:int,
        blur:int,
    ):
        nonlocal i
        name = stack_names[i]
        processed_stack = stack_dict[name]

        for idx in range(pipeline.count()):
            process_name = pipeline.item(idx).text()

            if process_name == "Gaussian blur" and use_blur.value:
                processed_stack = np.stack([
                    cv.GaussianBlur(slice_, (blur,blur), 0)
                    for slice_ in processed_stack
                ])

            if process_name == "Threshold" and use_threshold.value:
                processed_stack = (processed_stack > threshold).astype(np.uint8) * 255

            if process_name == "CLAHE" and use_clahe.value:
                clahe = cv.createCLAHE(clipLimit=5)
                processed_stack = np.stack([
                    clahe.apply(slice_)
                    for slice_ in processed_stack
                ])

        viewer.layers.remove(viewer.layers[stack_names[i]]) 

        viewer.add_image(
            processed_stack,
            name = name,
            colormap="gray",
        )

        restructure_layers()


    # divier widgets
    # TODO: Think of a way to turn these into a reusable function
    divider1 = Label(value="---------- Preprocessing Options ----------")
    divider2 = Label(value="---------- Pipeline order ----------")

    # checkbox widgets
    use_threshold = CheckBox(text="Threshold", value=False)
    use_blur = CheckBox(text="Blur", value=False)
    use_clahe = CheckBox(text="CLAHE", value=False)

    #rearrangeable cards
    pipeline = QListWidget()
    pipeline.addItems([
        "Gaussian blur",
        "Threshold",
        "CLAHE"
    ])

    pipeline.setDragDropMode(
        QAbstractItemView.InternalMove
    )

    #Buttons for the jansonius mapping
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

        x_scale = 237 / 15
        y_scale = 22 / 2

        fovea_row = 192
        fovea_col = 384

        rows = fovea_row - y_scale * y
        cols = fovea_col + x_scale * x

        scaled_coords = np.column_stack((rows, cols))

        jansonius_map = viewer.add_points(
            data = scaled_coords,
            name = "Jansonius mappings",
            face_color = "red",
            size = 7
        )

    # Combining the radius widgets for the jansonius mapping
    jansonius_range = Container(
        widgets=[
            SpinBox(value=4, min=4, max=30, label="Min"),
            SpinBox(value=20, min=4, max=30, label="Max"),
        ],
        layout="horizontal",
    )
    jansonius_widget.insert(1, jansonius_range)

    # Combining the widgets into one container
    io_container = Container(widgets=[save_lines, load_lines, next_stack, prev_stack])
    preprocessing_container = Container(
        widgets=[
            preprocessing_widgets,
            divider1,
            use_threshold,
            use_blur,
            use_clahe,
            divider2,
        ]
    )

    # Adding the pipeline widget to the container
    # TODO: make it look better
    preprocessing_container.native.layout().addWidget(pipeline)

    # Create a dock for widgets to the right side
    viewer.window.add_dock_widget(
        widget=io_container,
        name="Control panel",
        area="right",
    )
    viewer.window.add_dock_widget(
        widget = jansonius_widget,
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






