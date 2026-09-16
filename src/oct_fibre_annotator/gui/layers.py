import numpy as np


def create_layers(viewer, stack, name):
    viewer.add_image(
        stack,
        name = name,
        colormap = "gray",
    )

    # Defining layers outside for global uses
    # Add the layer for the jansonius mapping
    jansonius_map = viewer.add_points(
        data = [],
        name = "Jansonius mappings",
        face_color = "red",
        size = 1
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

    return jansonius_map, onh_layer, fovea_layer, lines_layer


# Function for reordering the layers in a specific order:
    # lines_layer
    # jansonius_map
    # onh plot
    # fovea plot
    # image stack
def restructure_layers(viewer, jansonius_map, onh_layer, fovea_layer, lines_layer):
    # move the layer for fovea layer to the top
    viewer.layers.move(
        viewer.layers.index(fovea_layer),
        len(viewer.layers),
    )
    # place ohn layer on top of fovea layer
    viewer.layers.move(
        viewer.layers.index(onh_layer),
        len(viewer.layers),
    )
    # place jansonius on top of onh layer
    viewer.layers.move(
        viewer.layers.index(jansonius_map),
        len(viewer.layers),
    )
    # lines_layer will be on top of jansonius_map
    viewer.layers.move(
        viewer.layers.index(lines_layer),
        len(viewer.layers),
    )
    # ensure that the lines_layer is selected
    viewer.layers.selection.active = lines_layer

