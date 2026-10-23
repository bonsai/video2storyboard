"""MediaPipe Tasks API wrapper compatible with the storyboard pose pipeline."""
from __future__ import annotations

import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarksConnections,
    RunningMode,
)
from mediapipe.tasks.python.vision.core.image import Image, ImageFormat

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
_MIN_MODEL_SIZE = 1_000_000

_POSE_LANDMARK_NAMES = [
    "NOSE", "LEFT_EYE_INNER", "LEFT_EYE", "LEFT_EYE_OUTER",
    "RIGHT_EYE_INNER", "RIGHT_EYE", "RIGHT_EYE_OUTER", "LEFT_EAR",
    "RIGHT_EAR", "MOUTH_LEFT", "MOUTH_RIGHT", "LEFT_SHOULDER",
    "RIGHT_SHOULDER", "LEFT_ELBOW", "RIGHT_ELBOW", "LEFT_WRIST",
    "RIGHT_WRIST", "LEFT_PINKY", "RIGHT_PINKY", "LEFT_INDEX",
    "RIGHT_INDEX", "LEFT_THUMB", "RIGHT_THUMB", "LEFT_HIP",
    "RIGHT_HIP", "LEFT_KNEE", "RIGHT_KNEE", "LEFT_ANKLE",
    "RIGHT_ANKLE", "LEFT_HEEL", "RIGHT_HEEL", "LEFT_FOOT_INDEX",
    "RIGHT_FOOT_INDEX",
]
_POSE_CONNECTIONS = tuple(
    (int(connection.start), int(connection.end))
    for connection in PoseLandmarksConnections.POSE_LANDMARKS
)


class _TasksPose:
    """Wrap Tasks API results in the legacy result shape expected by nodes."""

    def __init__(
        self,
        static_image_mode: bool = True,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self._model_path = self._resolve_model_path()
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self._model_path),
            running_mode=RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)

    @staticmethod
    def _resolve_model_path() -> str:
        """Use a configured model, repository model, or download to user cache."""
        configured = os.environ.get("VIDEO2STORYBOARD_POSE_MODEL")
        if configured:
            path = Path(configured).expanduser()
            if not path.is_file():
                raise FileNotFoundError(
                    f"VIDEO2STORYBOARD_POSE_MODEL does not point to a file: {path}"
                )
            if path.stat().st_size < _MIN_MODEL_SIZE:
                raise ValueError(f"Pose model file is too small or invalid: {path}")
            return str(path.resolve())

        repo_root = Path(__file__).resolve().parents[3]
        local_model = repo_root / "models" / "pose_landmarker_lite.task"
        if local_model.is_file() and local_model.stat().st_size >= _MIN_MODEL_SIZE:
            return str(local_model.resolve())

        cache_dir = Path.home() / ".cache" / "video2storyboard" / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cached_model = cache_dir / "pose_landmarker_lite.task"
        if cached_model.is_file() and cached_model.stat().st_size >= _MIN_MODEL_SIZE:
            return str(cached_model.resolve())

        fd, temporary_name = tempfile.mkstemp(
            prefix="pose_landmarker_lite.", suffix=".download", dir=cache_dir
        )
        os.close(fd)
        temporary_path = Path(temporary_name)
        try:
            urllib.request.urlretrieve(_MODEL_URL, temporary_path)
            if temporary_path.stat().st_size < _MIN_MODEL_SIZE:
                raise RuntimeError("Downloaded MediaPipe pose model is unexpectedly small")
            temporary_path.replace(cached_model)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
        return str(cached_model.resolve())

    def process(self, rgb_image: Any):
        """Run pose detection on a contiguous RGB NumPy array."""
        if rgb_image is None:
            return _SimpleResult(None)
        image = np.ascontiguousarray(rgb_image)
        mp_image = Image(image_format=ImageFormat.SRGB, data=image)
        return _SimpleResult(self._landmarker.detect(mp_image))

    def close(self):
        self._landmarker.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class _SimpleResult:
    """Expose result.pose_landmarks.landmark for existing graph nodes."""

    def __init__(self, tasks_result):
        self.pose_landmarks = self._convert(tasks_result) if tasks_result else None

    @staticmethod
    def _convert(tasks_result):
        if not tasks_result.pose_landmarks:
            return None
        landmarks = []
        for point in tasks_result.pose_landmarks[0]:
            class Landmark:
                __slots__ = ("x", "y", "z", "visibility")
            landmark = Landmark()
            landmark.x = float(point.x)
            landmark.y = float(point.y)
            landmark.z = float(point.z)
            landmark.visibility = float(point.visibility)
            landmarks.append(landmark)

        class LandmarkList:
            __slots__ = ("landmark",)
        result = LandmarkList()
        result.landmark = landmarks
        return result


def get_tasks_pose(
    static_image_mode: bool = True,
    model_complexity: int = 1,
    smooth_landmarks: bool = True,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
) -> _TasksPose:
    """Factory with the legacy constructor signature."""
    return _TasksPose(
        static_image_mode=static_image_mode,
        model_complexity=model_complexity,
        smooth_landmarks=smooth_landmarks,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )


def get_pose_connections() -> Iterable[tuple[int, int]]:
    """Return integer landmark connection pairs."""
    return _POSE_CONNECTIONS


def get_landmark_name(index: int) -> str:
    """Return landmark name by index (0-32)."""
    if 0 <= index < len(_POSE_LANDMARK_NAMES):
        return _POSE_LANDMARK_NAMES[index]
    return f"LANDMARK_{index}"



# Public helpers for the dedicated graph worker. Keep the legacy wrapper above
# available while the graph implementation is split into smaller modules.
import mediapipe as mp
from mediapipe.tasks.python.vision import RunningMode


def create_pose_landmarker(*, running_mode=RunningMode.IMAGE, num_poses: int = 1):
    """Create a Tasks API PoseLandmarker; the caller owns and closes it."""
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=_TasksPose._resolve_model_path()),
        running_mode=running_mode,
        num_poses=num_poses,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return PoseLandmarker.create_from_options(options)


def pose_connections() -> list[tuple[int, int]]:
    """Return landmark connections as plain integer pairs."""
    return list(_POSE_CONNECTIONS)


def landmarks_to_records(landmarks) -> list[dict[str, Any]]:
    """Convert normalized Tasks landmarks to the stable JSON record shape."""
    return [
        {
            "index": index,
            "name": get_landmark_name(index),
            "x": float(point.x),
            "y": float(point.y),
            "z": float(point.z),
            "visibility": float(getattr(point, "visibility", 1.0)),
            "presence": float(getattr(point, "presence", 1.0)),
        }
        for index, point in enumerate(landmarks)
    ]
