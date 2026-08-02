import cv2 as cv
import numpy as np
from pathlib import Path

# Input:
#   OCT slices with the structure of WF**_W_****_***.tiff.png
#   1165 slices belonging to 24 patients
# Output:
#   A dictionary of numpy stacks containing the images
#   The stack with the dimension of (number_of_slices, height, width)
#   The slices are stored in ascending order

# Takes in a path to the dataset
# Returns an array of distinct entry names
# TODO: validation on the data
def create_keys(path:Path) -> list[str]:
    keys = []
    for p in path.iterdir():
        key = str(p).split(".tiff")[0]
        if key not in keys:
            keys.append(key)
    return keys

# Takes in a path to the dataset
# Reteurns a dictionary of numpy stacks
# TODO: shorten the function so that it only iterates over the path once
# TODO: add the return type for the dictionary
def create_stack_dict(path:Path):
    stack_dict = dict()
    keys = create_keys(path)
    paths = sorted(path.iterdir(), key = lambda path: int(path.stem.split("_Z")[1].split(".tif")[0]))
    for p in paths:
        img = cv.imread(str(p))
        if img is None:
            raise Exception
        # TODO: this part can be shorten down for sure
        # Getting the key again can't be an effective way
        key = str(p).split(".tiff")[0]
        if key in keys:
            stack_dict.setdefault(key, []).append(img)
    for key in stack_dict:
        stack_dict[key] = np.stack(stack_dict[key])
    return stack_dict


