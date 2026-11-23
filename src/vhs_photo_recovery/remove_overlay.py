import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .settings import INPAINT_RADIUS


@dataclass(frozen=True)
class InpaintMask:
    """Parameters for mask application."""
    image_dimensions: tuple[int, int]
    mask_regions: tuple[tuple[int, int, int, int], ...]


def load_inpaint_mask(path: Path) -> InpaintMask:
    """Load and validate an inpainting mask from a JSON file."""
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise ValueError(f"Inpaint mask not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read inpaint mask: {path}") from exc

    if not isinstance(data, dict):
        raise ValueError("Inpaint mask must be a JSON object")

    size = data.get("image_dimensions")
    mask_regions = data.get("mask_regions")

    if (
        not isinstance(size, list)
        or len(size) != 2
        or any(type(value) is not int or value <= 0 for value in size)
    ):
        raise ValueError(
            "image_dimensions must contain two positive integers [width, height]"
        )

    if not isinstance(mask_regions, list) or not mask_regions:
        raise ValueError("mask_regions must contain at least one rectangle")

    width, height = size
    validated_regions = []

    for index, region in enumerate(mask_regions, start=1):
        if (
            not isinstance(region, list)
            or len(region) != 4
            or any(type(value) is not int for value in region)
        ):
            raise ValueError(
                f"Region {index} must contain four integer coordinates"
            )

        left, top, right, bottom = region

        if not (0 <= left < right < width):
            raise ValueError(
                f"Region {index} has invalid horizontal coordinates"
            )

        if not (0 <= top < bottom < height):
            raise ValueError(
                f"Region {index} has invalid vertical coordinates"
            )

        validated_regions.append(tuple(region))

    return InpaintMask(
        image_dimensions=(width, height),
        mask_regions=tuple(validated_regions),
    )



def overlay_mask(
    image: np.ndarray,
    config: InpaintMask,
) -> np.ndarray:
    """Create a mask scaled to the current image dimensions."""
    height, width = image.shape[:2]

    if not height or not width:
        raise ValueError("Image has no pixels")

    reference_width, reference_height = config.image_dimensions

    mask = np.zeros((height, width), dtype=np.uint8)

    for left, top, right, bottom in config.mask_regions:
        start = (
            round(left * width / reference_width),
            round(top * height / reference_height),
        )
        end = (
            round(right * width / reference_width),
            round(bottom * height / reference_height),
        )

        cv2.rectangle(
            mask,
            start,
            end,
            255,
            thickness=-1,
        )

    return mask



def remove_overlay(
    image: np.ndarray,
    config: InpaintMask,
) -> np.ndarray:
    """Remove the configured overlays using OpenCV inpainting."""
    mask = overlay_mask(image, config)

    return cv2.inpaint(
        image,
        mask,
        INPAINT_RADIUS,
        cv2.INPAINT_TELEA,
    )
