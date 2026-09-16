from pathlib import Path
from oct_fibre_annotator.io.main import create_stack_dict
from oct_fibre_annotator.gui.main import create_app
import napari
def main():
    # DATA_PATH = Path("/mnt/c/Users/vyblo/Downloads/full_dataset/")
    DATA_PATH = Path("/Users/henphan/Desktop/UNI/Y2/Y2S2/OmnissaHorizonSharing/partial_data/")
    OUT_PATH = Path("/Users/henphan/Documents/GitHub/fibre-ui/data/")
    
    print("OCT Annotator App")
    stack_dict = create_stack_dict(DATA_PATH)
    create_app(stack_dict, OUT_PATH)
    napari.run()
