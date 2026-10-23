"""Create a pose overlay layer image (PNG + SVG) from a single frame.

Reuses src/video2storyboard/pose_render.render_pose_artifacts so the overlay
matches the storyboard pipeline output exactly. Never modifies the source frame.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2

from .pose_tasks import get_tasks_pose, get_pose_connections, get_landmark_name


def make_layer_image(
    frame_path: str | Path,
    output_dir: str | Path,
    frame_id: str = "layer",
) -> dict[str, Any]:
    """Render one pose overlay layer image (PNG + transparent SVG skeleton).

    Returns dict with status ('detected'|'not_detected'|'error') and paths.
    Source image is not modified; outputs are written under output_dir.
    """
    source = Path(frame_path).expanduser()
    out = Path(output_dir)
    if not source.is_file():
        return {"status": "error", "overlay_png": "", "overlay_svg": "", "error": f"Frame not found: {source}"}

    image = cv2.imread(str(source))
    if image is None:
        return {"status": "error", "overlay_png": "", "overlay_svg": "", "error": f"Cannot decode frame: {source}"}

    from .pose_render import render_pose_artifacts

    pose_api = get_tasks_pose(static_image_mode=True, model_complexity=1,
                              min_detection_confidence=0.5)
    connections = list(get_pose_connections())
    try:
        with pose_api as pose:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            import numpy as np
            if not rgb.flags["C_CONTIGUOUS"]:
                rgb = np.ascontiguousarray(rgb)
            result = pose.process(rgb)
            if not result.pose_landmarks:
                return {
                    "status": "not_detected",
                    "overlay_png": "",
                    "overlay_svg": "",
                    "error": None,
                }

            landmarks = [
                {
                    "index": i,
                    "name": get_landmark_name(i),
                    "x": float(p.x),
                    "y": float(p.y),
                    "z": float(p.z),
                    "visibility": float(p.visibility),
                }
                for i, p in enumerate(result.pose_landmarks.landmark)
            ]
            return render_pose_artifacts(
                image, landmarks, connections, out, frame_id
            ) | {"status": "detected"}
    except Exception as exc:  # noqa: BLE001 - report worker error, keep going
        return {"status": "error", "overlay_png": "", "overlay_svg": "", "error": str(exc)}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Create pose overlay layer image (PNG + SVG).")
    parser.add_argument("--frame", required=True, help="Input frame PNG/JPG")
    parser.add_argument("--output-dir", required=True, help="Directory for layer PNG/SVG")
    parser.add_argument("--frame-id", default="layer", help="Output file id prefix")
    args = parser.parse_args()
    result = make_layer_image(args.frame, args.output_dir, args.frame_id)
    print(result)


if __name__ == "__main__":
    main()