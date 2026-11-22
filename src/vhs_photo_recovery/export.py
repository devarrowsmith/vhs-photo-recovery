from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from .settings import (
    CONTACT_BACKGROUND_GRAY,
    CONTACT_CAPTION_HEIGHT,
    CONTACT_LABEL_COLOR_BGR,
    CONTACT_LABEL_FONT_SCALE,
    CONTACT_LABEL_OFFSET_X,
    CONTACT_LABEL_OFFSET_Y,
    CONTACT_LABEL_THICKNESS,
    CONTACT_MARGIN,
    CONTACT_SHEET_COLUMNS,
    CONTACT_THUMBNAIL_HEIGHT,
    CONTACT_THUMBNAIL_WIDTH,
)


def make_contact_sheet(paths: list[Path], destination: Path, columns: int = CONTACT_SHEET_COLUMNS) -> None:
    """Save photographs and build a contact sheet."""
    if not paths:
        return

    rows = math.ceil(len(paths) / columns)
    sheet = np.full((rows * (CONTACT_THUMBNAIL_HEIGHT + CONTACT_CAPTION_HEIGHT + CONTACT_MARGIN) + CONTACT_MARGIN, columns * (CONTACT_THUMBNAIL_WIDTH + CONTACT_MARGIN) + CONTACT_MARGIN, 3), CONTACT_BACKGROUND_GRAY, dtype=np.uint8)
    for i, path in enumerate(paths):
        image = cv2.imread(str(path))
        if image is None:
            continue
        h, w = image.shape[:2]
        factor = min(CONTACT_THUMBNAIL_WIDTH / w, CONTACT_THUMBNAIL_HEIGHT / h)
        scaled = cv2.resize(image, (max(1, round(w * factor)), max(1, round(h * factor))), interpolation=cv2.INTER_AREA)
        x = CONTACT_MARGIN + (i % columns) * (CONTACT_THUMBNAIL_WIDTH + CONTACT_MARGIN)
        y = CONTACT_MARGIN + (i // columns) * (CONTACT_THUMBNAIL_HEIGHT + CONTACT_CAPTION_HEIGHT + CONTACT_MARGIN)
        ox, oy = x + (CONTACT_THUMBNAIL_WIDTH - scaled.shape[1]) // 2, y + (CONTACT_THUMBNAIL_HEIGHT - scaled.shape[0]) // 2
        sheet[oy:oy + scaled.shape[0], ox:ox + scaled.shape[1]] = scaled
        cv2.putText(sheet, path.stem, (x + CONTACT_LABEL_OFFSET_X, y + CONTACT_THUMBNAIL_HEIGHT + CONTACT_LABEL_OFFSET_Y), cv2.FONT_HERSHEY_SIMPLEX, CONTACT_LABEL_FONT_SCALE, CONTACT_LABEL_COLOR_BGR, CONTACT_LABEL_THICKNESS, cv2.LINE_AA)
    cv2.imwrite(str(destination), sheet)
