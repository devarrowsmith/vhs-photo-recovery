
"""Batch enhancement of photographs recovered from video."""

import argparse
from datetime import datetime
from pathlib import Path

import cv2

from .remove_overlay import overlay_mask, remove_overlay
from .settings import DEFAULT_SHARPEN_STRENGTH, IMAGE_SUFFIXES, JPG_QUALITY
from .sharpen import sharpen


def unique_output_path(source: Path, preview: bool) -> Path:
    """Find an unused timestamped output directory."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    label = "enhanced-preview" if preview else "enhanced"

    base = source.parent / f"{label}-{timestamp}"
    candidate = base
    counter = 2

    while candidate.exists():
        candidate = source.parent / f"{label}-{timestamp}-{counter}"
        counter += 1

    return candidate


def enhance_directory(
    source: Path,
    output: Path | None = None,
    *,
    strength: float = DEFAULT_SHARPEN_STRENGTH,
    preview: bool = False,
) -> Path:
    """Remove overlays and sharpen photographs in a directory."""
    if not source.is_dir():
        raise ValueError(f"Input folder does not exist: {source}")

    if strength < 0:
        raise ValueError("Sharpen strength must be non-negative")

    images = sorted(
        path
        for path in source.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )

    if not images:
        raise ValueError(f"No PNG/JPG images found in: {source}")

    if output is None:
        output = unique_output_path(source, preview)
    elif output.exists() and (
        not output.is_dir() or any(output.iterdir())
    ):
        raise ValueError(f"Output directory is not empty: {output}")

    output.mkdir(parents=True, exist_ok=True)

    if preview:
        images = images[:1]

    for index, path in enumerate(images, start=1):
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)

        if image is None:
            print(f"Warning: could not read {path.name}")
            continue

        cleaned = remove_overlay(image)

        result = sharpen(cleaned, strength)

        destination = output / path.name

        params = (
            [cv2.IMWRITE_JPEG_QUALITY, JPG_QUALITY]
            if path.suffix.lower() in {".jpg", ".jpeg"}
            else []
        )

        if not cv2.imwrite(str(destination), result, params):
            raise OSError(f"Failed to save image: {destination}")

        if preview:
            mask = overlay_mask(image)

            cv2.imwrite(
                str(output / "overlay-mask.png"),
                mask,
            )

            comparison = cv2.hconcat([image, result])

            cv2.imwrite(
                str(output / "before-after.jpg"),
                comparison,
                [cv2.IMWRITE_JPEG_QUALITY, JPG_QUALITY],
            )

        print(f"[{index}/{len(images)}] {path.name}", flush=True)

    print(f"Done: {output}")
    return output


def main() -> None:
    """Run the image enhancement command."""
    parser = argparse.ArgumentParser(
        prog="vhs-enhance",
        description=(
            "Remove camera overlays and sharpen recovered photographs."
        ),
    )

    parser.add_argument(
        "photos",
        type=Path,
        help="Directory containing recovered PNG or JPG images",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory (default: timestamped directory)",
    )

    parser.add_argument(
        "--strength",
        type=float,
        default=DEFAULT_SHARPEN_STRENGTH,
        help="Sharpening strength (0 disables sharpening)",
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Process one photo and save a before/after comparison",
    )

    args = parser.parse_args()

    try:
        enhance_directory(
            args.photos,
            args.output,
            strength=args.strength,
            preview=args.preview,
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
