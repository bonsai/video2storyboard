"""MediaPipe Tasks API wrapper for Pose Landmarker.

Provides a drop-in replacement for the old `mp.solutions.pose` interface.
Converts Tasks API output to the landmark format used by render_pose_artifacts.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, PoseLandmarksConnections
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.core.image import Image, ImageFormat


# MediaPipe Pose landmark names (33 landmarks) — same as old mp.solutions.pose.PoseLandmark
_POSE_LANDMARK_NAMES = [
    "NOSE",
    "LEFT_EYE_INNER",
    "LEFT_EYE",
    "LEFT_EYE_OUTER",
    "RIGHT_EYE_INNER",
    "RIGHT_EYE",
    "RIGHT_EYE_OUTER",
    "LEFT_EAR",
    "RIGHT_EAR",
    "MOUTH_LEFT",
    "MOUTH_RIGHT",
    "LEFT_SHOULDER",
    "RIGHT_SHOULDER",
    "LEFT_ELBOW",
    "RIGHT_ELBOW",
    "LEFT_WRIST",
    "RIGHT_WRIST",
    "LEFT_PINKY",
    "RIGHT_PINKY",
    "LEFT_INDEX",
    "RIGHT_INDEX",
    "LEFT_THUMB",
    "RIGHT_THUMB",
    "LEFT_HIP",
    "RIGHT_HIP",
    "LEFT_KNEE",
    "RIGHT_KNEE",
    "LEFT_ANKLE",
    "RIGHT_ANKLE",
    "LEFT_HEEL",
    "RIGHT_HEEL",
    "LEFT_FOOT_INDEX",
    "RIGHT_FOOT_INDEX",
]

# Pose connections from old API — 32 connections
_POSE_CONNECTIONS = tuple(
    (c.start, c.end) for c in PoseLandmarksConnections.POSE_LANDMARKS
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
        self._model_path = self._resolve_model_path()
        running_mode = PoseLandmarkerOptions.running_mode.IMAGE
        opts = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self._model_path),
            running_mode=running_mode,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
        )
        self._landmarker = PoseLandmarker.create_from_options(opts)

    @staticmethod
    def _resolve_model_path() -> str:
        """Resolve the .task model path.

        Priority:
        1. VIDEO2STORYBOARD_POSE_MODEL environment variable
        2. models/pose_landmarker.task relative to this file's parent (repo root)
        3. Fallback: download or raise
        """
        env = os.environ.get("VIDEO2STORYBOARD_POSE_MODEL")
        if env and Path(env).is_file():
            return str(Path(env).resolve())

        # Default: repo_root/models/pose_landmarker.task
        # __file__ is src/video2storyboard/work/pose/pose_tasks.py.
        repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        default = repo_root / "models" / "pose_landmarker.task"
        if default.is_file():
            return str(default)

        raise FileNotFoundError(
            "Pose Landmarker model (.task) not found. "
            "Set VIDEO2STORYBOARD_POSE_MODEL or place pose_landmarker.task at models/pose_landmarker.task"
        )

    def process(self, rgb_image: Any):
        """Run pose detection on an RGB numpy array.

        Returns an object compatible with old `mp.solutions.pose.Pose` process result:
        - .pose_landmarks: list of NormalizedLandmark objects (or None)
        """
        # MediaPipe Tasks expects RGB, channels=3, contiguous
        if rgb_image is None:
            return _SimpleResult(None)

        # Ensure correct format
        img = rgb_image
        if not img.flags["C_CONTIGUOUS"]:
            img = np.ascontiguousarray(img)
        mp_image = Image(image_format=ImageFormat.SRGB, data=img)
        result = self._landmarker.detect(mp_image)
        return _SimpleResult(result)

    def close(self):
        try:
            self._landmarker.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class _SimpleResult:
    """Mimic old mp.solutions.pose result: .pose_landmarks list or None."""

    def __init__(self, tasks_result):
        self.pose_landmarks = self._convert(tasks_result) if tasks_result else None

    @staticmethod
    def _convert(tasks_result):
        if not tasks_result.pose_landmarks:
            return None
        # Tasks returns list of poses (each pose is list of 33 NormalizedLandmark)
        # Old API returns a single NormalizedLandmarkList with .landmark attribute
        # We return a list of landmark objects with .x, .y, .z, .visibility
        pose = tasks_result.pose_landmarks[0]
        landmarks = []
        for i, p in enumerate(pose):
            # Create a simple object with required attributes
            class L:
                __slots__ = ("x", "y", "z", "visibility")
            l = L()
            l.x = float(p.x)
            l.y = float(p.y)
            l.z = float(p.z)
            l.visibility = float(p.visibility)
            landmarks.append(l)
        # Wrap in a simple container with .landmark list
        class LandmarkList:
            __slots__ = ("landmark",)
        lst = LandmarkList()
        lst.landmark = landmarks
        return lst


def get_tasks_pose(
    static_image_mode: bool = True,
    model_complexity: int = 1,
    smooth_landmarks: bool = True,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
) -> _TasksPose:
    """Factory function mimicking mp.solutions.pose.Pose()"""
    return _TasksPose(
        static_image_mode=static_image_mode,
        model_complexity=model_complexity,
        smooth_landmarks=smooth_landmarks,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )


# Re-export connections for rendering
def get_pose_connections() -> Iterable[tuple[int, int]]:
    """Return POSE_CONNECTIONS compatible with old mp.solutions.pose.POSE_CONNECTIONS"""
    return _POSE_CONNECTIONS


def get_landmark_name(index: int) -> str:
    """Return landmark name by index (0-32)"""
    if 0 <= index < len(_POSE_LANDMARK_NAMES):
        return _POSE_LANDMARK_NAMES[index]
    return f"LANDMARK_{index}"


# Import numpy lazily
try:
    import numpy as np
except Exception:
    pass
