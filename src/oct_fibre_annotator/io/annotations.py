from pathlib import Path

import numpy as np


def save_annotations(output_path: Path, lines, colours) -> None:
    output_path.parent.mkdir(parents=True, exist_ok = True)

    with open(output_path, "w") as f:
        f.write("r,g,b,y1,x1,y2,x2\n")
        for line, colour in zip(lines, colours):
            start, end = line
            r,g,b,a = colour
            f.write("{},{},{},{},{},{},{},{}\n".format(r,g,b,a,start[0], start[1], end[0], end[1]))


def load_annotations(output_path: Path):
    data = np.loadtxt(output_path, delimiter=",", skiprows=1)
    lines = data[:,4:8].reshape(-1,2,2)
    colours = data[:,:4]
    return lines, colours
