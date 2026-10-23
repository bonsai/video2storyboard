"""MediaPipe pose overlay renderers for offline storyboard and live preview."""
from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Any, Iterable


def render_pose_artifacts(
    image_bgr: Any,
    landmarks: list[dict[str, Any]],
    connections: Iterable[tuple[int, int]],
    output_dir: str | Path,
    frame_id: str,
) -> dict[str, str]:
    """Write a source-frame PNG preview and a transparent SVG skeleton overlay."""
    import cv2

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    height, width = image_bgr.shape[:2]
    points: dict[int, tuple[int, int]] = {}
    for item in landmarks:
        x = float(item.get("x", 0.0))
        y = float(item.get("y", 0.0))
        visibility = float(item.get("visibility", 1.0))
        if visibility < 0.35 or not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            continue
        points[int(item.get("index", len(points)))] = (round(x * (width - 1)), round(y * (height - 1)))

    # Pose landmark order is the MediaPipe index order; callers include index explicitly.
    preview = image_bgr.copy()
    lines: list[str] = []
    for start, end in connections:
        if start in points and end in points:
            p1, p2 = points[start], points[end]
            cv2.line(preview, p1, p2, (40, 220, 80), 2, cv2.LINE_AA)
            lines.append(
                f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" '
                'stroke="#28dc50" stroke-width="3" stroke-linecap="round" />'
            )
    for x, y in points.values():
        cv2.circle(preview, (x, y), 4, (40, 80, 255), -1, cv2.LINE_AA)
        lines.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#ff5028" />')

    png_path = out / f"{frame_id}-pose-overlay.png"
    svg_path = out / f"{frame_id}-pose-overlay.svg"
    if not cv2.imwrite(str(png_path), preview):
        raise RuntimeError(f"Could not write pose preview PNG: {png_path}")
    svg_path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><title>{html.escape(frame_id)} pose overlay</title>'
        + "".join(lines) + "</svg>\n",
        encoding="utf-8",
    )
    return {"overlay_png": str(png_path), "overlay_svg": str(svg_path)}


def run_webcam(camera_index: int = 0, mirror: bool = True) -> None:
    """Open a local webcam and render live MediaPipe pose landmarks with OpenCV."""
    import cv2
    import mediapipe as mp

    pose_api = mp.solutions.pose
    drawing = mp.solutions.drawing_utils
    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open webcam index {camera_index}")
    try:
        with pose_api.Pose(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as pose:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if mirror:
                    frame = cv2.flip(frame, 1)
                result = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if result.pose_landmarks:
                    drawing.draw_landmarks(
                        frame, result.pose_landmarks, pose_api.POSE_CONNECTIONS,
                        landmark_drawing_spec=drawing.DrawingSpec(
                            color=(40, 80, 255), thickness=2, circle_radius=3
                        ),
                        connection_drawing_spec=drawing.DrawingSpec(
                            color=(40, 220, 80), thickness=2
                        ),
                    )
                cv2.imshow("video2storyboard - MediaPipe Pose (press q to quit)", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
    finally:
        capture.release()
        cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview MediaPipe Pose from a local webcam.")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index (default: 0)")
    parser.add_argument("--no-mirror", action="store_true", help="Disable mirror display")
    args = parser.parse_args()
    run_webcam(args.camera, mirror=not args.no_mirror)


if __name__ == "__main__":
    main()
