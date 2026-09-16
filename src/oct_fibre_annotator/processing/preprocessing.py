import cv2 as cv
import numpy as np


def preprocess_stack(
    stack,
    pipeline,
    threshold: int,
    blur: int,
    use_blur: bool,
    use_threshold: bool,
    use_clahe: bool,
):
    processed_stack = stack

    for process_name in pipeline:
        if process_name == "Gaussian blur" and use_blur:
            processed_stack = np.stack([
                cv.GaussianBlur(slice_, (blur,blur), 0)
                for slice_ in processed_stack
            ])

        if process_name == "Threshold" and use_threshold:
            processed_stack = (processed_stack > threshold).astype(np.uint8) * 255

        if process_name == "CLAHE" and use_clahe:
            clahe = cv.createCLAHE(clipLimit=5)
            processed_stack = np.stack([
                clahe.apply(slice_)
                for slice_ in processed_stack
            ])

    return processed_stack
