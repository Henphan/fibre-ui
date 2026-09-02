import numpy as np
from shapely.geometry import Point, LineString

from rpy2.robjects import FloatVector, DataFrame
from rpy2.robjects.packages import importr


def sample_line(start, end, spacing=5):
    """
    Sample points along a straight annotation segment.

    start, end: (row, col)
    spacing: approximate spacing between sampled points in pixels
    """
    start = np.array(start, dtype=float)
    end = np.array(end, dtype=float)

    length = np.linalg.norm(end - start)
    n = max(2, int(np.ceil(length / spacing)) + 1)

    return np.linspace(start, end, n)


def positional_error(annotation, jansonius_curve, spacing=5):
    """
    Calculate mean distance between sampled annotation points
    and the Jansonius curve.

    annotation: [(row1, col1), (row2, col2)]
    jansonius_curve: array of shape (N, 2) in (row, col)
    """

    sampled_points = sample_line(
        annotation[0],
        annotation[1],
        spacing
    )

    # Shapely expects (x, y), so convert (row, col) -> (col, row)
    curve_xy = [(col, row) for row, col in jansonius_curve]
    curve = LineString(curve_xy)

    distances = []

    for row, col in sampled_points:
        point = Point(col, row)
        distances.append(point.distance(curve))

    return np.mean(distances)

def generate_jansonius_maps(
    fovea,
    onh,
    r_min=4,
    r_max=40,
    r_step=0.1,
):
    """
    Generate Jansonius trajectories for psi0 = -180 ... 179.

    fovea: (row, col)
    onh:   (row, col)

    Returns:
        dict where:
            key   = psi0
            value = numpy array of (row, col) coordinates
    """

    vf = importr("visualFields")

    fovea_row, fovea_col = fovea
    onh_row, onh_col = onh

    # Calculate image scaling
    x_scale = (onh_col - fovea_col) / 15
    y_scale = (onh_row - fovea_row) / 2

    # Same radial values used for every trajectory
    r = FloatVector(np.arange(r_min, r_max, r_step))

    mappings = {}

    for psi0 in range(-180, 180):

        path = vf.bundlePath(psi0)

        psi = path(r)

        rpsi = DataFrame({
            "r": r,
            "psi": psi,
        })

        coords = vf.jpolar2cart(rpsi)

        x = np.asarray(coords.rx2("x"))
        y = np.asarray(coords.rx2("y"))

        # Convert Jansonius coordinates -> image coordinates
        cols = x_scale * x + fovea_col
        rows = y_scale * y + fovea_row

        mappings[psi0] = np.column_stack((rows, cols))

    return mappings

annotation = [
    (188.14688110351562, 200.1124267578125),
    (161.47982788085938,222.10589599609375),
]


if __name__ == "__main__":
    errors = {}

    maps = generate_jansonius_maps((192,384), (168,618))
    for psi0 in maps:
        curve = maps[psi0]
        errors[psi0] = positional_error(annotation=annotation, jansonius_curve=curve)

    for candidate in sorted(errors.items(), key=lambda item: item[1])[:3]:
        print(candidate)
