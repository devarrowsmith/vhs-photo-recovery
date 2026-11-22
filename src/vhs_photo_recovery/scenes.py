from __future__ import annotations

import csv
from pathlib import Path

import cv2


def detect_scenes(video_path: Path, threshold: float, min_seconds: float) -> list[tuple[float, float]]:
    """Scene detection."""
    try:
        from scenedetect import ContentDetector, SceneManager, open_video
    except ImportError as exc:
        raise RuntimeError("Install dependencies first: uv sync") from exc
    stream = open_video(str(video_path))
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=round(stream.frame_rate * min_seconds)))
    print("Detecting scene changes (this reads the whole video)…", flush=True)
    manager.detect_scenes(video=stream)
    found = [(a.get_seconds(), b.get_seconds()) for a, b in manager.get_scene_list()]
    if not found:
        cap = cv2.VideoCapture(str(video_path))
        duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1.0)
        cap.release()
        if duration <= 0:
            raise RuntimeError("Could not determine video duration.")
        found = [(0.0, duration)]
    return found

def read_scenes(csv_path: Path) -> list[tuple[float, float]]:
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    scenes = []
    for row in rows:
        start, end = float(row["start_seconds"]), float(row["end_seconds"])
        if start < 0 or end <= start:
            raise ValueError(f"Invalid scene: {row}")
        scenes.append((start, end))
    return scenes

def write_scenes(path: Path, scenes: list[tuple[float, float]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start_seconds", "end_seconds"])
        for start, end in scenes:
            writer.writerow([f"{start:.3f}", f"{end:.3f}"])
