from pathlib import Path

from magicgui import magicgui
from magicgui.widgets import Container

from oct_fibre_annotator.io.annotations import load_annotations, save_annotations


def create_control_panel(lines_layer, output_dir, get_stack_name, next_stack, prev_stack):
    # Callback function for the "Save lines" button
    # Clicking the button will save the coordinates of all lines on the screen
    # Coordinates will be written to a csv file
    @magicgui(call_button="Save lines")
    def save_lines() -> None:
        lines = lines_layer.data
        colours = lines_layer.edge_color

        # When no line is drawn
        if len(lines) == 0:
            print("No lines to save.")
            return

        output_path = output_dir / Path("{}_lines.csv".format(get_stack_name()))
        save_annotations(output_path, lines, colours)

    # Callback function for loading the lines
    # Assumes that the line is saved using the format from above
    # TODO: Exception for when the file does not exist
    @magicgui(call_button="Load lines")
    def load_lines() -> None:
        output_path = output_dir / Path("{}_lines.csv".format(get_stack_name()))
        lines, colours = load_annotations(output_path)

        lines_layer.data = []

        # Add each of the line with the given colour
        for line in lines:
            lines_layer.add(line, shape_type="line")
        lines_layer.edge_color = colours


    return Container(widgets=[save_lines, load_lines, next_stack, prev_stack])
