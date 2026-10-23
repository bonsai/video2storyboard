"""Worker nodes for the video2storyboard graph.

Optional ML dependencies are loaded lazily. A missing optional backend is reported
as a structured worker error rather than silently fabricating an observation.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

from .state import VideoState
from ...pose.pose_tasks import get_tasks_pose, get_pose_connections, get_landmark_name


def _error(state: VideoState, worker: str, message: str) -> list[dict[str, Any]]:
    # The state reducer appends this worker-local error to concurrent worker errors.
    return [{"worker": worker, "message": message}]


def _events_path(state: VideoState) -> Path:
    return Path(state.get("output_dir", "outputs")) / state.get("run_id", "run") / "events.jsonl"


def append_event(state: VideoState, event: dict[str, Any]) -> None:
    """Append a structured worker event for the current run."""
    path = _events_path(state)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def ingest_video(state: VideoState) -> VideoState:
    path = Path(state.get("source_video", "")).expanduser()
    if not path.is_file():
        return {"status": "failed", "errors": _error(state, "ingest_video", f"Video file not found: {path}")}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError("OpenCV could not open video")
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()
        duration = frames / fps if fps > 0 else None
        metadata = {"fps": fps, "frame_count": frames, "width": width, "height": height,
                    "duration_seconds": duration, "aspect_ratio": width / height if height else None}
    except Exception as exc:
        return {"status": "failed", "errors": _error(state, "ingest_video", str(exc))}
    return {"source_sha256": digest, "source_id": state.get("source_id") or path.stem,
            "run_id": state.get("run_id") or str(uuid.uuid4()), "metadata": metadata,
            "errors": state.get("errors", []), "status": "running"}


def video2png(state: VideoState) -> VideoState:
    source = Path(state["source_video"]).expanduser()
    out = Path(state.get("output_dir", "outputs")) / (state.get("run_id", "run") + "/frames")
    out.mkdir(parents=True, exist_ok=True)
    interval = float(state.get("config", {}).get("frame_interval_seconds", 1.0))
    if interval <= 0:
        return {"errors": _error(state, "video2png", "frame_interval_seconds must be > 0")}
    try:
        import cv2
        cap = cv2.VideoCapture(str(source))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        frames: list[dict[str, Any]] = []
        index = 0
        next_at = 0.0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            timestamp = index / fps if fps > 0 else 0.0
            if timestamp + 1e-9 >= next_at:
                name = f"frame-{len(frames):06d}.png"
                target = out / name
                if not cv2.imwrite(str(target), frame):
                    raise RuntimeError(f"Could not write frame: {target}")
                height, width = frame.shape[:2]
                frames.append({"frame_id": f"f{len(frames):06d}", "timestamp_seconds": round(timestamp, 3),
                               "image": str(target), "width": width, "height": height,
                               "aspect_ratio": width / height if height else None})
                next_at += interval
            index += 1
        cap.release()
        return {"frames": frames, "errors": state.get("errors", [])}
    except Exception as exc:
        return {"errors": _error(state, "video2png", str(exc))}


def eye_pose_mp(state: VideoState) -> VideoState:
    try:
        import cv2
        import numpy as np
        results = []
        pose_api = get_tasks_pose(static_image_mode=True, model_complexity=1,
                                  min_detection_confidence=0.5)
        with pose_api as pose:
            connections = list(get_pose_connections())
            for frame in state.get("frames", []):
                image = cv2.imread(frame["image"])
                if image is None:
                    results.append({"frame_id": frame["frame_id"], "timestamp_seconds": frame["timestamp_seconds"],
                                    "status": "unreadable_image", "landmarks": None})
                    continue
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                if not rgb.flags["C_CONTIGUOUS"]:
                    rgb = np.ascontiguousarray(rgb)
                result = pose.process(rgb)
                landmarks = None
                if result.pose_landmarks:
                    landmarks = [{"index": i, "name": get_landmark_name(i),
                                  "x": float(p.x), "y": float(p.y), "z": float(p.z),
                                  "visibility": float(p.visibility)}
                                 for i, p in enumerate(result.pose_landmarks.landmark)]
                status = "detected" if landmarks else "not_detected"
                record = {"frame_id": frame["frame_id"], "timestamp_seconds": frame["timestamp_seconds"],
                          "status": status, "landmarks": landmarks, "image_width": frame.get("width"),
                          "image_height": frame.get("height")}
                append_event(state, {"worker": "eye_pose_mp", "event": "pose_result", "frame_id": frame["frame_id"], "status": status})
                if not landmarks:
                    append_event(state, {"worker": "eye_pose_mp", "event": "pose_not_detected", "frame_id": frame["frame_id"]})
                    results.append(record)
                    continue
                if landmarks:
                    try:
                        from ...pose.pose_render import render_pose_artifacts
                        overlay_dir = Path(state.get("output_dir", "outputs")) / state.get("run_id", "run") / "pose-overlays"
                        record.update(render_pose_artifacts(image, landmarks, connections,
                                                            overlay_dir, frame["frame_id"]))
                        status = "overlay_written"
                    except Exception as render_exc:
                        # Keep successful landmarks even if visual export fails.
                        record["overlay_error"] = str(render_exc)
                        status = "overlay_error"
                    append_event(state, {"worker": "eye_pose_mp", "event": "pose_overlay", "frame_id": frame["frame_id"], "status": status})
                if status == "error":
                    record["status"] = "error"
                results.append(record)
        return {"pose_results": results}
    except Exception as exc:
        return {"pose_results": [], "errors": _error(state, "eye_pose_mp", f"MediaPipe unavailable/failed: {exc}")}


def eye_composition_cv2(state: VideoState) -> VideoState:
    results = []
    try:
        import cv2
        for frame in state.get("frames", []):
            image = cv2.imread(frame["image"])
            if image is None:
                results.append({"frame_id": frame["frame_id"], "status": "unreadable_image"})
                continue
            h, w = image.shape[:2]
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            results.append({"frame_id": frame["frame_id"], "timestamp_seconds": frame["timestamp_seconds"],
                            "status": "measured", "width": w, "height": h,
                            "aspect_ratio": w / h if h else None,
                            "mean_luminance": float(gray.mean()),
                            "edge_density": float((edges > 0).mean()),
                            "background_context": "not_inferred_by_cv2",
                            "note": "These are image measurements, not semantic background labels."})
        return {"composition_results": results}
    except Exception as exc:
        return {"composition_results": [], "errors": _error(state, "eye_composition_cv2", str(exc))}


def eye_meaning_vlm(state: VideoState) -> VideoState:
    """Provider-neutral VLM hook. Set a project adapter via config['vlm_callable']."""
    adapter = state.get("config", {}).get("vlm_callable")
    if not callable(adapter):
        return {"meaning_results": [], "errors": _error(state, "eye_meaning_vlm",
                "No VLM adapter configured; set config['vlm_callable'] to a callable(frame_record) -> dict.")}
    results = []
    for frame in state.get("frames", []):
        try:
            observation = adapter(frame)
            results.append({"frame_id": frame["frame_id"], "timestamp_seconds": frame["timestamp_seconds"],
                            "status": "described", "observation": observation})
        except Exception as exc:
            results.append({"frame_id": frame["frame_id"], "timestamp_seconds": frame["timestamp_seconds"],
                            "status": "error", "error": str(exc)})
    return {"meaning_results": results}


def ear_stt_whisper(state: VideoState) -> VideoState:
    """Transcribe extracted audio with faster-whisper when installed."""
    source = Path(state["source_video"]).expanduser()
    audio_path = Path(state.get("output_dir", "outputs")) / (state.get("run_id", "run") + "/audio.wav")
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["ffmpeg", "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000",
                        str(audio_path)], check=True, capture_output=True, text=True)
        from faster_whisper import WhisperModel
        model_name = state.get("config", {}).get("whisper_model", "base")
        model = WhisperModel(model_name, device=state.get("config", {}).get("whisper_device", "cpu"),
                             compute_type=state.get("config", {}).get("whisper_compute_type", "int8"))
        segments, info = model.transcribe(str(audio_path), vad_filter=True)
        rows = [{"start_seconds": float(s.start), "end_seconds": float(s.end),
                 "text": s.text.strip(), "language": info.language, "model": model_name}
                for s in segments]
        return {"transcript_segments": rows}
    except Exception as exc:
        return {"transcript_segments": [], "errors": _error(state, "ear_stt_whisper",
                f"Whisper/ffmpeg unavailable or failed: {exc}")}


def hand_storyboard_builder(state: VideoState) -> VideoState:
    pose = {x["frame_id"]: x for x in state.get("pose_results", [])}
    composition = {x["frame_id"]: x for x in state.get("composition_results", [])}
    meaning = {x["frame_id"]: x for x in state.get("meaning_results", [])}
    panels = []
    for frame in state.get("frames", []):
        fid = frame["frame_id"]
        panels.append({
            "panel_id": f"panel-{len(panels) + 1:04d}",
            "frame_id": fid,
            "timestamp_seconds": frame["timestamp_seconds"],
            "image": os.path.relpath(frame["image"], Path(state.get("output_dir", "outputs")) / state.get("run_id", "run")),
            "visual": {"pose": pose.get(fid), "composition": composition.get(fid),
                       "meaning": meaning.get(fid)},
            "audio": [s for s in state.get("transcript_segments", [])
                      if s["start_seconds"] <= frame["timestamp_seconds"] <= s["end_seconds"]],
            "human_edit": None,
        })
    return {"storyboard": {"schema_version": "1.0", "video_id": state.get("source_id"),
            "source_sha256": state.get("source_sha256"), "run_id": state.get("run_id"),
            "metadata": state.get("metadata", {}), "panels": panels,
            "analysis_errors": state.get("errors", [])}}


def paper_html_svg(state: VideoState) -> VideoState:
    storyboard = state.get("storyboard", {})
    output = Path(state.get("output_dir", "outputs")) / state.get("run_id", "run")
    output.mkdir(parents=True, exist_ok=True)
    json_path, html_path, svg_path = output / "storyboard.json", output / "storyboard.html", output / "storyboard.svg"
    json_path.write_text(json.dumps(storyboard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    import html
    cards = []
    svg_panels = []
    for i, panel in enumerate(storyboard.get("panels", [])):
        desc = panel.get("visual", {}).get("meaning", {}).get("observation", {})
        description = desc.get("description", "") if isinstance(desc, dict) else str(desc or "")
        safe_desc = html.escape(str(description))
        safe_image = html.escape(str(panel.get("image", "")), quote=True)
        cards.append(f'<article><h2>{html.escape(panel["panel_id"])}</h2><p>{panel["timestamp_seconds"]:.2f}s</p><img src="{safe_image}" alt="Storyboard frame"><p>{safe_desc}</p></article>')
        y = i * 180
        svg_panels.append(f'<g transform="translate(0,{y})"><rect width="960" height="164" rx="8" fill="#f3f4f6" stroke="#9ca3af"/><text x="18" y="28" font-size="18" font-weight="bold">{html.escape(panel["panel_id"])}</text><text x="18" y="54" font-size="14">{panel["timestamp_seconds"]:.2f}s</text><text x="18" y="88" font-size="14">{safe_desc[:100]}</text></g>')
    html_path.write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Storyboard Review</title><style>body{font-family:system-ui;margin:24px;background:#111827;color:#f9fafb}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}article{padding:12px;border:1px solid #4b5563;border-radius:10px}img{width:100%;aspect-ratio:16/9;object-fit:contain;background:#030712}</style><h1>Storyboard Review</h1><div class="grid">' + "".join(cards) + '</div></html>', encoding="utf-8")
    height = max(180, len(svg_panels) * 180)
    svg_path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}"><title>Storyboard</title>' + "".join(svg_panels) + '</svg>', encoding="utf-8")
    return {"artifacts": {"json": str(json_path), "html": str(html_path), "svg": str(svg_path)}}


def validate_storyboard(state: VideoState) -> VideoState:
    errors = list(state.get("errors", []))
    sb = state.get("storyboard", {})
    if not isinstance(sb.get("panels"), list):
        errors.append({"worker": "validate_storyboard", "message": "storyboard.panels must be a list"})
    seen = set()
    for panel in sb.get("panels", []):
        if panel.get("panel_id") in seen:
            errors.append({"worker": "validate_storyboard", "message": f"duplicate panel_id: {panel.get('panel_id')}"})
        seen.add(panel.get("panel_id"))
        if not isinstance(panel.get("timestamp_seconds"), (int, float)):
            errors.append({"worker": "validate_storyboard", "message": f"invalid timestamp: {panel.get('panel_id')}"})
    return {"errors": errors, "status": "completed" if not errors else "completed_with_errors"}
