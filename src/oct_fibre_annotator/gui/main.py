import napari

def create_app(stack_dict):
    viewer = napari.Viewer(title = "OCT Fibre Annotator")

    for key in stack_dict:
        stack = stack_dict[key]
        viewer.add_image(
            stack,
            name = key,
            colormap = "gray",
        )

    napari.run()
