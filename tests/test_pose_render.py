from pathlib import Path

import cv2
import numpy as np

from video2storyboard.pose_render import render_pose_artifacts


def test_render_pose_artifacts_writes_png_and_transparent_svg(tmp_path: Path):
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    landmarks = [
        {"index": 0, "name": "NOSE", "x": 0.25, "y": 0.3, "z": 0.0, "visibility": 0.99},
        {"index": 1, "name": "LEFT_EYE_INNER", "x": 0.5, "y": 0.6, "z": 0.0, "visibility": 0.99},
    ]

    artifacts = render_pose_artifacts(image, landmarks, [(0, 1)], tmp_path, "f000001")

    png = Path(artifacts["overlay_png"])
    svg = Path(artifacts["overlay_svg"])
    assert png.is_file()
    assert cv2.imread(str(png)).shape[:2] == (100, 200)
    assert svg.is_file()
    text = svg.read_text(encoding="utf-8")
    assert 'width="200" height="100"' in text
    assert "<line " in text
    assert "<circle " in text
    assert "f000001 pose overlay" in text
