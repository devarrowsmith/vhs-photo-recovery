import cv2
import numpy as np

from .settings import DEFAULT_SHARPEN_STRENGTH, SHARPEN_BLUR_SIGMA


def sharpen(
    image: np.ndarray,
    strength: float = DEFAULT_SHARPEN_STRENGTH,
) -> np.ndarray:
    """Sharpen image edges without changing image dimensions."""
    if strength < 0:
        raise ValueError("Sharpen strength must be non-negative")

    if strength == 0:
        return image.copy()

    blurred = cv2.GaussianBlur(
        image,
        (0, 0),
        SHARPEN_BLUR_SIGMA,
    )

    return cv2.addWeighted(
        image,
        1.0 + strength,
        blurred,
        -strength,
        0,
    )
