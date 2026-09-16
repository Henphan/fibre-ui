from magicgui import magicgui

from oct_fibre_annotator.gui.layers import restructure_layers


def create_navigation(
    viewer, stack_dict, stack_names, jansonius_map, onh_layer, fovea_layer,
    lines_layer, reset_jansonius,
):
    i = 0

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

            # Reset the jansonius state
            reset_jansonius()


            # Reordering the layers
            restructure_layers(viewer, jansonius_map, onh_layer, fovea_layer, lines_layer)

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

            # Reset the jansonius state
            reset_jansonius()

            # Reordering the layers
            restructure_layers(viewer, jansonius_map, onh_layer, fovea_layer, lines_layer)

    def get_stack_name():
        return stack_names[i]

    return next_stack, prev_stack, get_stack_name
