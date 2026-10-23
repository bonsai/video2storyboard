"""Dance pipeline canonical IR (versioned JSON/JSONL).

IR is the stable interchange contract between Pipeline 1 (video -> Pose data)
and Pipeline 2 (dance data -> Blender backend).  It must NOT depend on
MediaPipe-specific output objects or Blender's ``bpy``.

Schema overview
---------------
::

    {
      "$schema": "video2storyboard-dance-ir-v1.0",
      "schema_version": "1.0",
      "source_video": "<abs path>",
      "source_id": "<stem or caller-supplied>",
      "source_sha256": "<hexdigest>",
      "interval": {"start_seconds": 140.0, "end_seconds": 225.0},
      "metadata": {
        "created_at": "<iso ts>",
        "fps": 30.0,
        "frame_interval_seconds": 1.0,
        "width": 640,
        "height": 480
      },
      "frames": [
        {
          "frame_id": "f000000",
          "timestamp_seconds": 140.0,
          "image_width": 640,
          "image_height": 480,
          "image_path": "<relative or abs>",
          "overlay": {"png": "...", "svg": "..."}
        }
      ],
      "poses": [
        {
          "frame_id": "f000000",
          "timestamp_seconds": 140.0,
          "image_width": 640,
          "image_height": 480,
          "status": "detected",          # detected | not_detected | unreadable_image | error | overlay_error
          "landmarks": [
            {"index": 0, "name": "NOSE", "x": ..., "y": ..., "z": ..., "visibility": ...}
          ],
          "overlay": {"png": "...", "svg": "..."},
          "error": null
        }
      ],
      "events": [
        {"event": "pose_result", "frame_id": "...", "status": "detected", "ts": "<iso>"}
      ],
      "errors": ["[worker] message"]
    }
"""
from __future__ import annotations

import datetime
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

IR_VERSION = "1.0"
IR_SCHEMA = "video2storyboard-dance-ir-v1.0"


@dataclass
class IRFrame:
    """Canonical per-frame representation."""
    frame_id: str
    timestamp_seconds: float
    image_width: int
    image_height: int
    image_path: str
    overlay: Dict[str, str] = field(default_factory=dict)


@dataclass
class IRPose:
    """Canonical per-frame pose result."""
    frame_id: str
    timestamp_seconds: float
    image_width: int
    image_height: int
    status: str  # detected | not_detected | unreadable_image | error | overlay_error
    landmarks: List[Dict[str, Any]] = field(default_factory=lambda: [])
    overlay: Dict[str, str] = field(default_factory=lambda: {})
    error: Optional[str] = None


@dataclass
class IREvent:
    """Canonical execution event."""
    event: str
    worker: str = "pose_processor"
    frame_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


@dataclass
class DanceIR:
    """Versioned IR container (serializable to JSON/JSONL)."""
    schema_version: str = IR_VERSION
    schema: str = IR_SCHEMA
    source_video: Optional[str] = None
    source_id: Optional[str] = None
    source_sha256: Optional[str] = None
    interval: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=lambda: {"created_at": datetime.datetime.now(datetime.UTC).isoformat()})
    frames: List[IRFrame] = field(default_factory=list)
    poses: List[IRPose] = field(default_factory=list)
    events: List[IREvent] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # --- builders ---------------------------------------------------------
    def add_frame(self, frame_id: str, timestamp_seconds: float, width: int,
                  height: int, image_path: str, overlay: Optional[Dict[str, str]] = None):
        self.frames.append(IRFrame(
            frame_id=frame_id, timestamp_seconds=timestamp_seconds,
            image_width=width, image_height=height, image_path=image_path,
            overlay=overlay or {})
        )

    def add_pose(self, pose: IRPose):
        self.poses.append(pose)
        self.events.append(IREvent(
            event="pose_result", worker="eye_pose_mp",
            frame_id=pose.frame_id, status=pose.status,
            message=pose.error))

    def add_event(self, **kw):
        self.events.append(IREvent(**kw))

    def add_error(self, worker: str, message: str):
        self.errors.append(f"[{worker}] {message}")

    # --- serialization ----------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "schema": self.schema,
            "source_video": self.source_video,
            "source_id": self.source_id,
            "source_sha256": self.source_sha256,
            "interval": self.interval,
            "metadata": self.metadata,
            "frames": [asdict(f) for f in self.frames],
            "poses": [asdict(p) for p in self.poses],
            "events": [asdict(e) for e in self.events],
            "errors": self.errors,
        }

    def to_json(self, pretty: bool = True) -> str:
        return json.dumps(self.to_dict(), indent=2 if pretty else None, ensure_ascii=False)

    def save(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(self.to_json(), encoding="utf-8")

    def append_events_jsonl(self, path: str | Path):
        """Append event list to a JSONL file (one event per line)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            for e in self.events:
                fh.write(json.dumps(asdict(e), ensure_ascii=False) + "\n")


# --- adapters -----------------------------------------------------------
def from_pipeline1_frames(frames: List[Dict[str, Any]], video_meta: Dict[str, Any],
                          interval: Dict[str, float]) -> DanceIR:
    """Build a DanceIR from Pipeline 1 frame manifest + metadata."""
    ir = DanceIR(
        source_id=video_meta.get("source_id"),
        interval=interval,
    )
    if "fps" in video_meta:
        ir.metadata["fps"] = video_meta["fps"]
    if "width" in video_meta:
        ir.metadata["width"] = video_meta["width"]
    if "height" in video_meta:
        ir.metadata["height"] = video_meta["height"]
    for f in frames:
        ir.add_frame(
            frame_id=f["frame_id"],
            timestamp_seconds=f["timestamp_seconds"],
            width=f.get("width", video_meta.get("width", 0)),
            height=f.get("height", video_meta.get("height", 0)),
            image_path=f.get("image", ""),
        )
    return ir


def ir_pose_from_record(record: Dict[str, Any]) -> IRPose:
    """Convert an eye_pose_mp record / Pipeline 2 pose result to IRPose."""
    overlay = {}
    if record.get("overlay_png"):
        overlay["png"] = record["overlay_png"]
    if record.get("overlay_svg"):
        overlay["svg"] = record["overlay_svg"]

    # Normalize landmarks to list of dicts with index, x, y, z, visibility
    landmarks = record.get("landmarks") or []
    if landmarks and not isinstance(landmarks, list):
        landmarks = [landmarks]
    # If landmarks is a dict mapping index->values, convert to list
    if isinstance(landmarks, dict):
        landmarks = [
            {"index": int(k), "x": float(v.get("x", 0)), "y": float(v.get("y", 0)),
             "z": float(v.get("z", 0)), "visibility": float(v.get("visibility", 1.0))}
            for k, v in landmarks.items()
        ]
    elif landmarks and isinstance(landmarks[0], dict) and "index" not in landmarks[0]:
        for i, lm in enumerate(landmarks):
            lm["index"] = i
            lm.setdefault("visibility", 1.0)

    return IRPose(
        frame_id=record.get("frame_id", ""),
        timestamp_seconds=float(record.get("timestamp_seconds", record.get("ts", 0))),
        image_width=int(record.get("image_width") or record.get("width") or 0),
        image_height=int(record.get("image_height") or record.get("height") or 0),
        status=record.get("status", "error"),
        landmarks=landmarks,
        overlay=overlay,
        error=record.get("overlay_error"),
    )
