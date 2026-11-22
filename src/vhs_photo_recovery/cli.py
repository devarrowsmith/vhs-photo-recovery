from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import RecoveryOptions, recover_video
from .settings import (
    DEFAULT_FRAMES_PER_PHOTO,
    DEFAULT_MIN_SCENE_SECONDS,
    DEFAULT_SCENE_THRESHOLD_SECONDS,
    DEFAULT_TRANSITION_TRIM_SECONDS,
)


def build_parser() -> argparse.ArgumentParser:
    """CLI command argument parser."""
    parser = argparse.ArgumentParser(
        prog="vhs-recover",
        description="Recover still photographs from videos of slideshows.",
    )
    parser.add_argument("video", type=Path, help="MP4 slideshow file")
    parser.add_argument("--output", type=Path, help="Output directory (default: output/<video name>)")
    parser.add_argument("--scenes", type=Path, help="Use an existing scene CSV instead of detecting")
    parser.add_argument("--detect-only", action="store_true", help="Write scene CSV without extracting photos")
    parser.add_argument("--threshold", type=float, default=DEFAULT_SCENE_THRESHOLD_SECONDS, help=f"Scene sensitivity: lower splits more; default {DEFAULT_SCENE_THRESHOLD_SECONDS}")
    parser.add_argument("--min-scene", type=float, default=DEFAULT_MIN_SCENE_SECONDS, help="Minimum scene length in seconds")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES_PER_PHOTO, help=f"Samples per photo; default {DEFAULT_FRAMES_PER_PHOTO}")
    parser.add_argument("--trim", type=float, default=DEFAULT_TRANSITION_TRIM_SECONDS, help="Seconds to avoid around transitions")
    parser.add_argument("--no-align", action="store_true", help="Disable global translation alignment")
    return parser


def main() -> None:
    """CLI command handler."""
    parser = build_parser()
    args = parser.parse_args()
    if not args.video.is_file():
        parser.error(f"Not a file: {args.video}")
    if args.scenes and not args.scenes.is_file():
        parser.error(f"Scene CSV not found: {args.scenes}")
    if args.frames < 1 or args.min_scene <= 0 or args.trim < 0:
        parser.error("--frames must be >= 1, --min-scene > 0, and --trim >= 0")

    recover_video(RecoveryOptions(
        video=args.video, output=args.output, scenes=args.scenes,
        detect_only=args.detect_only, threshold=args.threshold,
        min_scene=args.min_scene, frames=args.frames, trim=args.trim,
        align=not args.no_align,
    ))


if __name__ == "__main__":
    main()
