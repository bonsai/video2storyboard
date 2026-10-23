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
    """Open a local webcam and render live pose landmarks using MediaPipe Tasks."""
    import cv2
    from .pose_tasks import RunningMode, create_pose_landmarker, landmarks_to_records, mp, pose_connections

    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open webcam index {camera_index}")
    try:
        with create_pose_landmarker(running_mode=RunningMode.VIDEO) as landmarker:
            timestamp_ms = 0
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if mirror:
                    frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = landmarker.detect_for_video(mp_image, timestamp_ms)
                timestamp_ms += 33
                if result.pose_landmarks:
                    records = landmarks_to_records(result.pose_landmarks[0])
                    render_pose_artifacts(frame, records, pose_connections(), Path.cwd() / ".pose-preview", "live")
                    # Draw directly into the displayed frame; no files are needed for the preview.
                    points = {
                        int(item["index"]): (round(item["x"] * (frame.shape[1] - 1)),
                                              round(item["y"] * (frame.shape[0] - 1)))
                        for item in records
                        if float(item.get("visibility", 1.0)) >= 0.35
                        and 0 <= item["x"] <= 1 and 0 <= item["y"] <= 1
                    }
                    for start, end in pose_connections():
                        if start in points and end in points:
                            cv2.line(frame, points[start], points[end], (40, 220, 80), 2, cv2.LINE_AA)
                    for point in points.values():
                        cv2.circle(frame, point, 3, (40, 80, 255), -1, cv2.LINE_AA)
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
