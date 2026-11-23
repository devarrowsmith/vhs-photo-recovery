
import cv2
import numpy as np

from .settings import INPAINT_RADIUS, OVERLAY_REGIONS, REFERENCE_IMAGE_SIZE


def overlay_mask(image: np.ndarray) -> np.ndarray:
    """Create a mask covering the camera overlays."""
    height, width = image.shape[:2]

    if not height or not width:
        raise ValueError("Image has no pixels")

    reference_width, reference_height = REFERENCE_IMAGE_SIZE
    mask = np.zeros((height, width), dtype=np.uint8)

    for x1, y1, x2, y2 in OVERLAY_REGIONS:
        start = (
            round(x1 * width / reference_width),
            round(y1 * height / reference_height),
        )
        end = (
            round(x2 * width / reference_width),
            round(y2 * height / reference_height),
        )

        cv2.rectangle(mask, start, end, 255, thickness=-1)

    return mask


def remove_overlay(image: np.ndarray) -> np.ndarray:
    """Remove camera overlays by inpainting the masked regions."""
    mask = overlay_mask(image)

    return cv2.inpaint(
        image,
        mask,
        INPAINT_RADIUS,
        cv2.INPAINT_TELEA,
    )
