from pathlib import Path

from magicgui.widgets import Slider, Container, Label, CheckBox, SpinBox, FloatSpinBox
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
        # stack dict: dictionary where the key is the stack name and the value is the array of images
        # output path: where the csv containing the line coordinates are written to
    # Returns the Viewer object from napari
    # NOTE: Does it matter if we return the object or not? We do not even use it.

    # Defining the Viewer, which is the application as far as I know
    viewer = napari.Viewer(title="OCT Fibre Annotator")

    # Add the first stack of OCT scans into the application as a layer
    stack_names = list(stack_dict.keys())
    i = 0
    viewer.add_image(
        stack_dict[stack_names[i]],
        name = stack_names[i],
        colormap = "gray",
    )

    # Defining layers outside for global uses
    # Add the layer for the jansonius mapping
    jansonius_map = viewer.add_points(
        data = [],
        name = "Jansonius mappings",
        face_color = "red",
        size = 7
    )
    # adding the layers for onh and fovea points
    onh_layer = viewer.add_points(
        np.empty((0,2)),
        name = "ONH",
        size = 7,
    )
    fovea_layer = viewer.add_points(
        np.empty((0,2)),
        name = "Fovea",
        size = 7,
    )
    # Adding the line drawing layer
    # TODO: somehow remove this error regarding add_shapes()
    # NOTE: lines_layer is on top
    lines_layer = viewer.add_shapes(
        data = [],
        name = "Annotations",
        edge_color = "red",
    )
    # Auto-selecting the 'add line' feature for the user
    lines_layer.mode = "add_line"

    # Callback function for the "Save lines" button
    # Clicking the button will save the coordinates of all lines on the screen
    # Coordinates will be written to a csv file
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

    # Callback function for loading the lines
    # Assumes that the line is saved using the format from above
    # TODO: Exception for when the file does not exist
    @magicgui(call_button="Load lines")
    def load_lines() -> None:
        nonlocal i

        output_path = output_dir / Path("{}_lines.csv".format(stack_names[i]))
        data = np.loadtxt(output_path, delimiter=",", skiprows=1)
        lines = data[:,4:8].reshape(-1,2,2)
        colours = data[:,:4]

        lines_layer.data = []

        # Add each of the line with the given colour
        for line in lines:
            lines_layer.add(line, shape_type="line")
        lines_layer.edge_color = colours


    # Callback function for going to the next stack of images
    @magicgui(call_button="Next stack")
    def next_stack() -> None:
        nonlocal i

        # Bound checking for going to the next stack
        if i + 1 < len(stack_names):
            viewer.layers.remove(viewer.layers[stack_names[i]]) 

            i += 1

            # Add the new stack
            viewer.add_image(
                stack_dict[stack_names[i]],
                name = stack_names[i],
                colormap = "gray",
            )

            # Reordering the layers
            restructure_layers()

    # Callback function for going to the previous stack of images
    @magicgui(call_button="Previous stack")
    def prev_stack() -> None:
        nonlocal i

        # Bound checking for going to the previous stack
        if i - 1 >= 0:
            viewer.layers.remove(viewer.layers[stack_names[i]]) 

            i -= 1

            # Add the new stack
            viewer.add_image(
                stack_dict[stack_names[i]],
                name = stack_names[i],
                colormap = "gray",
            )

            # Reordering the layers
            restructure_layers()

    # Function for reordering the layers in a specific order:
        # lines_layer
        # jansonius_map
        # image stack
    def restructure_layers():
        # move the layer for jansonius mapping to the top
        viewer.layers.move(
            viewer.layers.index(jansonius_map),
            len(viewer.layers),
        )
        # move the layer for lines to the top
        # lines_layer will be on top of jansonius_map
        viewer.layers.move(
            viewer.layers.index(lines_layer),
            len(viewer.layers),
        )
        # ensure that the lines_layer is selected
        viewer.layers.selection.active = lines_layer

    # GUI for preprocessing
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


    # Defining dividers for the tabs 
    # TODO: Think of a way to turn these into a reusable function
    divider1 = Label(value="---------- Preprocessing Options ----------")
    divider2 = Label(value="---------- Pipeline order ----------")

    # checkbox widgets for the preprocessing tab
    use_threshold = CheckBox(text="Threshold", value=False)
    use_blur = CheckBox(text="Blur", value=False)
    use_clahe = CheckBox(text="CLAHE", value=False)

    #rearrangeable cards for the preprocessing tab
    pipeline = QListWidget()
    pipeline.addItems([
        "Gaussian blur",
        "Threshold",
        "CLAHE"
    ])

    pipeline.setDragDropMode(
        QAbstractItemView.InternalMove
    )

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
        rows = x_scale * x + select_fovea.fovea_x.value
        cols = y_scale * y + select_fovea.fovea_y.value
        # print(rows,cols)
        #
        # x_scale = 237 / 15
        # y_scale = 22 / 2
        #
        # fovea_row = 192
        # fovea_col = 384
        #
        # rows = fovea_row - y_scale * y
        # cols = fovea_col + x_scale * x
        #
        # print(rows,cols)
        #
        # return

        scaled_coords = np.column_stack((cols, rows))

        jansonius_map.data = scaled_coords

        restructure_layers()
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

    def on_onh_change(event):
        nonlocal waiting

        if waiting and len(onh_layer.data) == 1:
            waiting = False
            viewer.layers.selection.active = lines_layer
            lines_layer.mode = "add_line"
            # changing the values of the SpinBoxes
            y,x = onh_layer.data[0]
            select_onh.onh_x.value = int(x)
            select_onh.onh_y.value = int(y)

    def on_fovea_change(event):
        nonlocal waiting

        if waiting and len(fovea_layer.data) == 1:
            waiting = False
            viewer.layers.selection.active = lines_layer
            lines_layer.mode = "add_line"
            # changing the values of the SpinBoxes
            y,x = fovea_layer.data[0]
            select_fovea.fovea_x.value = int(x)
            select_fovea.fovea_y.value = int(y)

    # whenever fovea_layer/onh_layer .data changes, run on_fovea_change()
    fovea_layer.events.data.connect(on_fovea_change)
    onh_layer.events.data.connect(on_onh_change)

    # Combining the radius widgets for the jansonius mapping
    # FloatSpinBox is used because we are taking the range between the values by steps of 0.1 anyways
    jansonius_range = Container(
        widgets=[
            FloatSpinBox(value=4, min=4, max=30, label="Min"),
            FloatSpinBox(value=20, min=4, max=30, label="Max"),
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
        ],
        labels = False
    )

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






