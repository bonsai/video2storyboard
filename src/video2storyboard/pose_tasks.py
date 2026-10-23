"""Shared MediaPipe Tasks API helpers for Pose Landmarker."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.request import urlretrieve

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarksConnections,
    RunningMode,
)

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
LANDMARK_NAMES = (
    "NOSE", "LEFT_EYE_INNER", "LEFT_EYE", "LEFT_EYE_OUTER",
    "RIGHT_EYE_INNER", "RIGHT_EYE", "RIGHT_EYE_OUTER", "LEFT_EAR",
    "RIGHT_EAR", "MOUTH_LEFT", "MOUTH_RIGHT", "LEFT_SHOULDER",
    "RIGHT_SHOULDER", "LEFT_ELBOW", "RIGHT_ELBOW", "LEFT_WRIST",
    "RIGHT_WRIST", "LEFT_PINKY", "RIGHT_PINKY", "LEFT_INDEX",
    "RIGHT_INDEX", "LEFT_THUMB", "RIGHT_THUMB", "LEFT_HIP",
    "RIGHT_HIP", "LEFT_KNEE", "RIGHT_KNEE", "LEFT_ANKLE",
    "RIGHT_ANKLE", "LEFT_HEEL", "RIGHT_HEEL", "LEFT_FOOT_INDEX",
    "RIGHT_FOOT_INDEX",
)


def resolve_pose_model() -> Path:
    """Resolve configured model or download the official Lite model to the user cache."""
    configured = os.environ.get("VIDEO2STORYBOARD_POSE_MODEL")
    if configured:
        path = Path(configured).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"VIDEO2STORYBOARD_POSE_MODEL does not exist: {path}")
        return path

    cache = Path.home() / ".cache" / "video2storyboard" / "models"
    target = cache / "pose_landmarker_lite.task"
    if target.is_file() and target.stat().st_size > 1_000_000:
        return target

    cache.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".task.download")
    try:
        urlretrieve(MODEL_URL, temporary)
        if temporary.stat().st_size < 1_000_000:
            raise RuntimeError("Downloaded Pose Landmarker model is unexpectedly small")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def create_pose_landmarker(*, running_mode=RunningMode.IMAGE, num_poses: int = 1):
    """Create a Tasks API PoseLandmarker; caller owns and must close it."""
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(resolve_pose_model())),
        running_mode=running_mode,
        num_poses=num_poses,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return PoseLandmarker.create_from_options(options)


def pose_connections() -> list[tuple[int, int]]:
    """Return connections as plain integer pairs for renderer compatibility."""
    return [(int(edge.start), int(edge.end)) for edge in PoseLandmarksConnections.POSE_LANDMARKS]


def landmarks_to_records(landmarks) -> list[dict]:
    """Convert Tasks API normalized landmarks to the repository's stable record shape."""
    return [
        {
            "index": index,
            "name": LANDMARK_NAMES[index] if index < len(LANDMARK_NAMES) else f"LANDMARK_{index}",
            "x": float(point.x),
            "y": float(point.y),
            "z": float(point.z),
            "visibility": float(getattr(point, "visibility", 1.0)),
            "presence": float(getattr(point, "presence", 1.0)),
        }
        for index, point in enumerate(landmarks)
    ]


__all__ = [
    "mp", "RunningMode", "create_pose_landmarker", "pose_connections",
    "landmarks_to_records",
]
