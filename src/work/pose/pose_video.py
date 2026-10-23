"""Rainbow MediaPipe Pose overlay for offline video export and interactive preview."""
from __future__ import annotations

import argparse
import colorsys
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def rainbow_bgr(index: int, total: int) -> tuple[int, int, int]:
    """Map a connection index to a vivid rainbow color in OpenCV BGR order."""
    red, green, blue = colorsys.hsv_to_rgb((index / max(total, 1)) % 1.0, 0.95, 1.0)
    return round(blue * 255), round(green * 255), round(red * 255)


def draw_pose_rainbow(frame: Any, pose_landmarks: Any, connections: Any,
                      visibility_threshold: float = 0.35) -> Any:
    """Draw visible landmarks and rainbow-colored bones on a BGR frame."""
    import cv2
    height, width = frame.shape[:2]
    points = {}
    for index, point in enumerate(pose_landmarks.landmark):
        if float(getattr(point, "visibility", 1.0)) < visibility_threshold:
            continue
        x, y = float(point.x), float(point.y)
        if 0 <= x <= 1 and 0 <= y <= 1:
            points[index] = (round(x * (width - 1)), round(y * (height - 1)))
    edges = list(connections)
    for i, (start, end) in enumerate(edges):
        if start in points and end in points:
            cv2.line(frame, points[start], points[end], rainbow_bgr(i, len(edges)), 3, cv2.LINE_AA)
    for point in points.values():
        cv2.circle(frame, point, 3, (255, 255, 255), -1, cv2.LINE_AA)
    return frame


def _validate_paths(source: Path, output: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Input video not found: {source}")
    if source.resolve() == output.resolve():
        raise ValueError("Output path must differ from source video path.")
    output.parent.mkdir(parents=True, exist_ok=True)


def render_video_overlay(input_video: str | Path, output_video: str | Path, *,
                         visibility_threshold: float = 0.35, preserve_audio: bool = True,
                         model_complexity: int = 0, max_frames: int | None = None) -> dict[str, Any]:
    """Render a new MP4; optionally mux original audio with FFmpeg. Never edits source."""
    import cv2
    import mediapipe as mp
    source, output = Path(input_video).expanduser().resolve(), Path(output_video).expanduser().resolve()
    _validate_paths(source, output)
    if preserve_audio and shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required for audio preservation; use preserve_audio=False for silent output.")
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Could not open input video: {source}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if fps <= 0 or width <= 0 or height <= 0:
        cap.release()
        raise RuntimeError("Input video has invalid FPS or dimensions.")
    temp_dir = Path(tempfile.mkdtemp(prefix="v2s-pose-"))
    silent = temp_dir / "render-silent.mp4"
    writer = cv2.VideoWriter(str(silent), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        cap.release()
        writer.release()
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError("Could not create output video writer.")
    count, pose_api = 0, mp.solutions.pose
    try:
        with pose_api.Pose(static_image_mode=False, model_complexity=model_complexity,
                           smooth_landmarks=True, min_detection_confidence=0.5,
                           min_tracking_confidence=0.5) as pose:
            while max_frames is None or count < max_frames:
                ok, frame = cap.read()
                if not ok:
                    break
                result = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if result.pose_landmarks:
                    draw_pose_rainbow(frame, result.pose_landmarks, pose_api.POSE_CONNECTIONS, visibility_threshold)
                writer.write(frame)
                count += 1
    finally:
        cap.release()
        writer.release()
    try:
        if preserve_audio:
            subprocess.run(["ffmpeg", "-y", "-i", str(silent), "-i", str(source),
                            "-map", "0:v:0", "-map", "1:a?", "-c:v", "copy",
                            "-c:a", "aac", "-shortest", str(output)],
                           check=True, capture_output=True, text=True)
        else:
            shutil.move(str(silent), str(output))
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"Video export failed: {getattr(exc, 'stderr', None) or exc}") from exc
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return {"input_video": str(source), "output_video": str(output), "fps": fps,
            "width": width, "height": height, "frames_written": count,
            "audio_preserved": preserve_audio}


def preview_video_toggle(input_video: str | Path, *, visibility_threshold: float = 0.35,
                         model_complexity: int = 0) -> None:
    """Preview a video; press P to toggle pose, Q or Esc to quit."""
    import cv2
    import mediapipe as mp
    source = Path(input_video).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Input video not found: {source}")
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Could not open input video: {source}")
    enabled, pose_api = True, mp.solutions.pose
    try:
        with pose_api.Pose(static_image_mode=False, model_complexity=model_complexity,
                           smooth_landmarks=True, min_detection_confidence=0.5,
                           min_tracking_confidence=0.5) as pose:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                result = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if enabled and result.pose_landmarks:
                    draw_pose_rainbow(frame, result.pose_landmarks, pose_api.POSE_CONNECTIONS, visibility_threshold)
                cv2.putText(frame, f"POSE {'ON' if enabled else 'OFF'} | P toggle | Q quit",
                            (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.imshow("video2storyboard rainbow pose preview", frame)
                key = cv2.waitKey(max(1, round(1000 / max(cap.get(cv2.CAP_PROP_FPS), 1)))) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("p"):
                    enabled = not enabled
    finally:
        cap.release()
        cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Rainbow MediaPipe Pose video overlay.")
    parser.add_argument("--input-video", required=True)
    parser.add_argument("--output-video")
    parser.add_argument("--preview", action="store_true", help="Play video and press P to toggle pose")
    parser.add_argument("--no-audio", action="store_true", help="Write silent MP4 without FFmpeg mux")
    parser.add_argument("--visibility-threshold", type=float, default=0.35)
    parser.add_argument("--model-complexity", type=int, choices=(0, 1, 2), default=0)
    args = parser.parse_args()
    if args.preview:
        preview_video_toggle(args.input_video, visibility_threshold=args.visibility_threshold,
                             model_complexity=args.model_complexity)
    else:
        if not args.output_video:
            parser.error("--output-video is required unless --preview is used")
        print(render_video_overlay(args.input_video, args.output_video,
                                   visibility_threshold=args.visibility_threshold,
                                   preserve_audio=not args.no_audio,
                                   model_complexity=args.model_complexity))


if __name__ == "__main__":
    main()
