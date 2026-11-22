from __future__ import annotations

import cv2
import numpy as np

from .settings import MAX_TRIM_FRACTION_OF_SCENE


def sample_frames(cap: cv2.VideoCapture, start: float, end: float, count: int, trim: float) -> list[np.ndarray]:
    """Sample frames from a scene, avoiding transition edges."""
    # Leave out transitions on BOTH sides, reducing trimming for very short scenes.
    safe_trim = min(trim, max(0.0, (end - start) * MAX_TRIM_FRACTION_OF_SCENE))
    a, b = start + safe_trim, end - safe_trim
    # Ensure timestamps stay strictly within the scene; never seek to the next scene.
    times = np.linspace(a, b, count + 2)[1:-1]
    images = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, float(t) * 1000)
        ok, frame = cap.read()
        if ok and frame is not None:
            images.append(frame)
    return images
