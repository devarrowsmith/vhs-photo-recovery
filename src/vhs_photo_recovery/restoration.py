from __future__ import annotations

import numpy as np


def median_composite(frames: list[np.ndarray]) -> np.ndarray:
    """Combine aligned frames into a single photograph."""
    return np.median(np.stack(frames, axis=0), axis=0).astype(np.uint8)
