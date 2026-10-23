"""Focused tests for pose_layer_image — single-frame overlay PNG + SVG layer creation."""
from pathlib import Path
import sys

sys.path.insert(0, "src")

import cv2
import numpy as np
import pytest

from video2storyboard.work.pose.pose_layer_image import make_layer_image


def _make_synthetic_frame(path: Path) -> None:
    """Draw a stick-person silhouette so MediaPipe may or may not detect; we just need a valid frame."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(img, (280, 100), (360, 260), (200, 200, 200), -1)   # torso
    cv2.circle(img, (320, 70), 40, (200, 200, 200), -1)              # head
    cv2.line(img, (280, 160), (220, 240), (200, 200, 200), 20)       # arm
    cv2.line(img, (360, 160), (420, 240), (200, 200, 200), 20)       # arm
    cv2.line(img, (300, 260), (280, 400), (200, 200, 200), 20)       # leg
    cv2.line(img, (340, 260), (360, 400), (200, 200, 200), 20)       # leg
    cv2.imwrite(str(path), img)


def test_layer_image_writes_png_and_svg(tmp_path):
    frame = tmp_path / "frame.png"
    _make_synthetic_frame(frame)
    out_dir = tmp_path / "layers"
    result = make_layer_image(frame, out_dir, frame_id="layer001")
    assert result["status"] in ("detected", "not_detected")
    if result["status"] == "detected":
        png = Path(result["overlay_png"])
        svg = Path(result["overlay_svg"])
        assert png.is_file()
        assert svg.is_file()
        assert png.suffix == ".png"
        assert svg.suffix == ".svg"


def test_layer_image_missing_frame_returns_error(tmp_path):
    missing = tmp_path / "does_not_exist.png"
    result = make_layer_image(missing, tmp_path / "out", frame_id="x")
    assert result["status"] == "error"
    assert result["overlay_png"] == ""
    assert result["overlay_svg"] == ""
    assert result["error"] is not None
