"""MediaPipe Tasks API implementation of the pose graph worker."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def eye_pose_mp(state: dict[str, Any]) -> dict[str, Any]:
    """Detect poses using MediaPipe Tasks and preserve the existing pose result contract."""
    try:
        import cv2
        from ..pose_tasks import (
            RunningMode, create_pose_landmarker, landmarks_to_records, mp, pose_connections,
        )

        results = []
        overlay_dir = (
            Path(state.get("output_dir", "outputs"))
            / state.get("run_id", "run")
            / "pose-overlays"
        )
        with create_pose_landmarker(running_mode=RunningMode.IMAGE) as landmarker:
            connections = pose_connections()
            for frame in state.get("frames", []):
                image = cv2.imread(frame["image"])
                record: dict[str, Any] = {
                    "frame_id": frame["frame_id"],
                    "timestamp_seconds": frame["timestamp_seconds"],
                    "image_width": int(frame.get("width", image.shape[1] if image is not None else 0)),
                    "image_height": int(frame.get("height", image.shape[0] if image is not None else 0)),
                }
                if image is None:
                    record.update({"status": "unreadable_image", "landmarks": None})
                    results.append(record)
                    continue

                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                detection = landmarker.detect(mp_image)
                landmarks = (
                    landmarks_to_records(detection.pose_landmarks[0])
                    if detection.pose_landmarks else None
                )
                record.update({
                    "status": "detected" if landmarks else "not_detected",
                    "landmarks": landmarks,
                })
                if landmarks:
                    try:
                        from ..pose_render import render_pose_artifacts
                        record.update(render_pose_artifacts(
                            image, landmarks, connections, overlay_dir, frame["frame_id"],
                        ))
                    except Exception as render_exc:
                        record["overlay_error"] = str(render_exc)
                results.append(record)
        return {"pose_results": results}
    except Exception as exc:
        return {
            "pose_results": [],
            "errors": [{
                "worker": "eye_pose_mp",
                "message": f"MediaPipe Tasks unavailable/failed: {exc}",
            }],
        }
