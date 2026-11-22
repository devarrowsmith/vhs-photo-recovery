from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2

from .alignment import align_frames
from .export import make_contact_sheet
from .frames import sample_frames
from .restoration import median_composite
from .scenes import detect_scenes, read_scenes, write_scenes
from .settings import (
    DEFAULT_FRAMES_PER_PHOTO,
    DEFAULT_MIN_SCENE_SECONDS,
    DEFAULT_SCENE_THRESHOLD_SECONDS,
    DEFAULT_TRANSITION_TRIM_SECONDS,
    JPG_QUALITY,
)


@dataclass(frozen=True)
class RecoveryOptions:
    video: Path
    output: Path | None = None
    scenes: Path | None = None
    detect_only: bool = False
    threshold: float = DEFAULT_SCENE_THRESHOLD_SECONDS
    min_scene: float = DEFAULT_MIN_SCENE_SECONDS
    frames: int = DEFAULT_FRAMES_PER_PHOTO
    trim: float = DEFAULT_TRANSITION_TRIM_SECONDS
    align: bool = True


def recover_video(options: RecoveryOptions) -> Path:
    """Recover each candidate scene."""

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    output = options.output or Path("output") / f"{options.video.stem}-{timestamp}"

    counter = 2
    base_output = output

    while output.exists():
        output = Path(f"{base_output}-{counter}")
        counter += 1

    output.mkdir(parents=True, exist_ok=True)

    scenes = (read_scenes(options.scenes) if options.scenes else detect_scenes(options.video, options.threshold, options.min_scene))
    scene_csv = output / "scenes.csv"
    write_scenes(scene_csv, scenes)
    print(f"Found {len(scenes)} candidate photos. Scene timings: {scene_csv}")
    if options.detect_only:
        return output

    restoration_dir, jpg_dir, frames_dir = (
        output / name for name in ("restorations", "jpgs", "comparison-frames")
    )
    for folder in (restoration_dir, jpg_dir, frames_dir):
        folder.mkdir(exist_ok=True)

    cap = cv2.VideoCapture(str(options.video))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {options.video}")
    thumbnails: list[Path] = []
    try:
        for index, (start, end) in enumerate(scenes, 1):
            frames = sample_frames(cap, start, end, options.frames, options.trim)
            if not frames:
                print(f"[{index}/{len(scenes)}] WARNING: no readable frames; skipped")
                continue
            basename = f"photo_{index:04d}"
            single = frames[len(frames) // 2]
            cv2.imwrite(str(frames_dir / (basename + ".jpg")), single,
                        [cv2.IMWRITE_JPEG_QUALITY, JPG_QUALITY])
            frames = align_frames(frames, options.align)
            recovered = median_composite(frames)
            cv2.imwrite(str(restoration_dir / (basename + ".png")), recovered)
            jpg_path = jpg_dir / (basename + ".jpg")
            cv2.imwrite(str(jpg_path), recovered, [cv2.IMWRITE_JPEG_QUALITY, JPG_QUALITY])
            thumbnails.append(jpg_path)
            print(f"[{index}/{len(scenes)}] {basename}: {len(frames)} frames, "f"{start:.1f}–{end:.1f}s", flush=True)
    finally:
        cap.release()

    make_contact_sheet(thumbnails, output / "contact-sheet.jpg")
    print(f"Extraction complete. Review {output / 'contact-sheet.jpg'} and compare restorations with comparison frames.")
    return output
