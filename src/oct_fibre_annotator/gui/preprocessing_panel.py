from magicgui import magicgui
from magicgui.widgets import CheckBox, Container, Label
from qtpy.QtWidgets import QListWidget, QAbstractItemView

from oct_fibre_annotator.gui.layers import restructure_layers
from oct_fibre_annotator.processing.preprocessing import preprocess_stack


def create_preprocessing_panel(
    viewer, stack_dict, get_stack_name, jansonius_map, onh_layer, fovea_layer, lines_layer,
):
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
        name = get_stack_name()
        processed_stack = preprocess_stack(
            stack_dict[name],
            [pipeline.item(idx).text() for idx in range(pipeline.count())],
            threshold,
            blur,
            use_blur=use_blur.value,
            use_threshold=use_threshold.value,
            use_clahe=use_clahe.value,
        )

        viewer.layers.remove(viewer.layers[get_stack_name()]) 

        viewer.add_image(
            processed_stack,
            name = name,
            colormap="gray",
        )

        restructure_layers(viewer, jansonius_map, onh_layer, fovea_layer, lines_layer)


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

    return preprocessing_container
