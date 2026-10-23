"""MediaPipe Tasks API wrapper for Pose Landmarker.

Provides a drop-in replacement for the old `mp.solutions.pose` interface.
Converts Tasks API output to the landmark format used by render_pose_artifacts.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.request import urlretrieve
from typing import Any, Iterable

import numpy as np
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarksConnections,
    RunningMode,
)
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.core.image import Image, ImageFormat

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)

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
    (int(c.start), int(c.end)) for c in PoseLandmarksConnections.POSE_LANDMARKS
)


class _TasksPose:
    """Internal class wrapping the Tasks API PoseLandmarker."""

    def __init__(
        self,
        static_image_mode: bool = True,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        # This compatibility adapter is used for sampled still frames.
        # Webcam preview uses the VIDEO running mode in its dedicated path.
        self._model_path = self._resolve_model_path()
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self._model_path),
            running_mode=RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)

    @staticmethod
    def _resolve_model_path() -> str:
        """Resolve a configured model or cache the official Lite model outside the repo."""
        configured = os.environ.get("VIDEO2STORYBOARD_POSE_MODEL")
        if configured:
            path = Path(configured).expanduser()
            if not path.is_file():
                raise FileNotFoundError(
                    f"VIDEO2STORYBOARD_POSE_MODEL does not exist: {path}"
                )
            return str(path.resolve())

        cache = Path.home() / ".cache" / "video2storyboard" / "models"
        target = cache / "pose_landmarker_lite.task"
        if target.is_file() and target.stat().st_size > 1_000_000:
            return str(target)

        cache.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".task.download")
        try:
            urlretrieve(MODEL_URL, temporary)
            if temporary.stat().st_size < 1_000_000:
                raise RuntimeError(
                    "Downloaded Pose Landmarker model is unexpectedly small"
                )
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return str(target)

    def process(self, rgb_image: Any):
        """Run pose detection on an RGB numpy array, preserving the legacy result shape."""
        if rgb_image is None:
            return _SimpleResult(None)
        image = rgb_image
        if not image.flags["C_CONTIGUOUS"]:
            image = np.ascontiguousarray(image)
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
    """Mimic the legacy .pose_landmarks.landmark result contract."""

    def __init__(self, tasks_result):
        self.pose_landmarks = self._convert(tasks_result) if tasks_result else None

    @staticmethod
    def _convert(tasks_result):
        if not tasks_result.pose_landmarks:
            return None
        pose = tasks_result.pose_landmarks[0]
        landmarks = []
        for point in pose:
            landmark = type("Landmark", (), {})()
            landmark.x = float(point.x)
            landmark.y = float(point.y)
            landmark.z = float(point.z)
            landmark.visibility = float(getattr(point, "visibility", 1.0))
            landmarks.append(landmark)
        return type("LandmarkList", (), {"landmark": landmarks})()


def get_tasks_pose(
    static_image_mode: bool = True,
    model_complexity: int = 1,
    smooth_landmarks: bool = True,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
) -> _TasksPose:
    """Factory function mimicking mp.solutions.pose.Pose()."""
    return _TasksPose(
        static_image_mode=static_image_mode,
        model_complexity=model_complexity,
        smooth_landmarks=smooth_landmarks,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )


def get_pose_connections() -> Iterable[tuple[int, int]]:
    """Return POSE_CONNECTIONS as plain integer pairs."""
    return _POSE_CONNECTIONS


def get_landmark_name(index: int) -> str:
    """Return the MediaPipe landmark name for index 0–32."""
    if 0 <= index < len(_POSE_LANDMARK_NAMES):
        return _POSE_LANDMARK_NAMES[index]
    return f"LANDMARK_{index}"
