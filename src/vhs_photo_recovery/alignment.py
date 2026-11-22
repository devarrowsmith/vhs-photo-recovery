from __future__ import annotations

import cv2
import numpy as np

from .settings import (
    ALIGNMENT_BLUR_KERNEL_SIZE,
    ALIGNMENT_EPSILON,
    ALIGNMENT_GAUSSIAN_FILTER_SIZE,
    ALIGNMENT_MAX_DIMENSION,
    ALIGNMENT_MAX_ITERATIONS,
    ALIGNMENT_MAX_SHIFT_FRACTION,
)


def align_frames(frames: list[np.ndarray], enabled: bool) -> list[np.ndarray]:
    """
    Align successive frames.
    """
    if not enabled or len(frames) < 2:
        return frames
    reference = frames[len(frames) // 2]
    # ECC is estimated at half resolution, then translated back to full size.
    h, w = reference.shape[:2]
    scale = min(1.0, ALIGNMENT_MAX_DIMENSION / max(w, h))
    def reduced_gray(frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if scale < 1.0:
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        return cv2.GaussianBlur(gray, ALIGNMENT_BLUR_KERNEL_SIZE, 0).astype(np.float32) / 255.0
    ref_gray = reduced_gray(reference)
    aligned = []
    for frame in frames:
        if frame is reference:
            aligned.append(frame)
            continue
        warp = np.eye(2, 3, dtype=np.float32)
        try:
            _, warp = cv2.findTransformECC(
                ref_gray,
                reduced_gray(frame),
                warp,
                cv2.MOTION_TRANSLATION,
                (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, ALIGNMENT_MAX_ITERATIONS, ALIGNMENT_EPSILON),
                None,
                ALIGNMENT_GAUSSIAN_FILTER_SIZE
            )
            shift = np.linalg.norm(warp[:, 2]) / scale
            if shift > ALIGNMENT_MAX_SHIFT_FRACTION * min(w, h):
                aligned.append(frame)  # absurd shift: safer to skip alignment
                continue
            warp[:, 2] /= scale
            aligned.append(cv2.warpAffine(
                frame, warp, (w, h),
                flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REFLECT
            ))
        except cv2.error: # pylint: disable=catching-non-exception
            aligned.append(frame)
    return aligned
