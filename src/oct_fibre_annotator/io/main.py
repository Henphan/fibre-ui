import cv2 as cv
import numpy as np
from pathlib import Path

# Input:
#   A folder containing image files and/or subfolders
#   A file is loaded as a single image, named after the file without its extension (img1.png -> img1)
#   A subfolder is loaded as a stack, named after the folder
#   Slices inside a subfolder are named by their number (1.png, 2.png, ...)
# Output:
#   A dictionary of numpy stacks containing the images
#   The stack with the dimension of (number_of_slices, height, width)
#   A single image is a stack with one slice
#   The slices are stored in ascending order

# Takes in a path to the dataset
# Returns an array of distinct entry names
# TODO: validation on the data
def create_keys(path:Path) -> list[str]:
    keys = []
    for p in path.iterdir():
        key = p.name.split("_Z")[0]
        if key not in keys:
            keys.append(key)
    return keys

# Takes in a path to an image
# Returns the image as a grayscale numpy array
def read_image(path:Path):
    img = cv.imread(str(path), cv.IMREAD_GRAYSCALE)
    if img is None:
        raise Exception
    return img

# Takes in a path to the dataset
# Reteurns a dictionary of numpy stacks
# TODO: add the return type for the dictionary
def create_stack_dict(path:Path):
    stack_dict = dict()
    for p in sorted(path.iterdir()):
        # folders keep their full name, files drop their extension (image2.jpg -> image2)
        key = p.name if p.is_dir() else p.name.split(".")[0]
        if key in stack_dict:
            raise Exception
        if p.is_dir():
            # slices are named by their number, e.g. 1.png, 2.png
            slice_paths = sorted(p.iterdir(), key = lambda s: int(s.name.split(".")[0]))
            stack_dict[key] = np.stack([read_image(s) for s in slice_paths])
        else:
            stack_dict[key] = np.stack([read_image(p)])
    return stack_dict


