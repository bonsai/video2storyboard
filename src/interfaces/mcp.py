"""Local-only stdio MCP server for OpenCode.

Run from the repository root with:
    PYTHONPATH=src python -m video2storyboard.interfaces.mcp
"""
from __future__ import annotations

import base64
import importlib.util
import json
import os
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("video2storyboard")


def _base_url() -> str:
    return os.environ.get("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")


def _request_json(url: str, payload: dict[str, Any] | None = None, timeout: int = 10) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("LM_STUDIO_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=data, headers=headers, method="GET" if payload is None else "POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _local_models() -> dict[str, Any]:
    """Read model inventory from the configured local LM Studio endpoint only."""
    try:
        result = _request_json(f"{_base_url()}/models", timeout=4)
        return {"reachable": True, "models": [item.get("id") for item in result.get("data", [])]}
    except Exception as exc:
        return {"reachable": False, "error": f"{type(exc).__name__}: {exc}", "models": []}


def _lm_studio_vlm(frame: dict[str, Any]) -> dict[str, Any]:
    model = os.environ.get("VIDEO2STORYBOARD_VLM_MODEL", "").strip()
    if not model:
        raise RuntimeError("Set VIDEO2STORYBOARD_VLM_MODEL to a vision-capable model ID from LM Studio /v1/models.")
    image_path = Path(str(frame.get("image", ""))).expanduser().resolve()
    if not image_path.is_file():
        raise FileNotFoundError(f"Frame image not found: {image_path}")
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    system_prompt = (
        "Analyze one sampled video frame for a storyboard. Describe only visible evidence. "
        "Return one JSON object with description, subjects, actions, setting, shot_type, "
        "camera_angle, composition, mood, and uncertainty. Do not infer identity or unsupported events."
    )
    user_prompt = (
        "Describe this frame concisely for storyboard continuity. Separate direct observations "
        "from uncertain interpretation. Return JSON only."
    )
    response = _request_json(
        f"{_base_url()}/chat/completions",
        {
            "model": model,
            "temperature": 0.1,
            "max_tokens": 700,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
                ]},
            ],
        },
        timeout=int(os.environ.get("VIDEO2STORYBOARD_VLM_TIMEOUT", "120")),
    )
    choices = response.get("choices", [])
    if not choices:
        raise RuntimeError("LM Studio response has no choices.")
    message = choices[0].get("message", {})
    raw = message.get("content", "")
    if isinstance(raw, list):
        raw = "".join(part.get("text", "") for part in raw if isinstance(part, dict))
    raw = str(raw).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3].strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        observation = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LM Studio returned invalid JSON: {exc}") from exc
    if not isinstance(observation, dict) or not isinstance(observation.get("description"), str):
        raise RuntimeError("VLM JSON must be an object with a string 'description' field.")
    return observation


@mcp.tool()
def video2storyboard_check_local() -> dict[str, Any]:
    """Check local Python dependencies, FFmpeg, and LM Studio models without reading video files."""
    packages = ["langgraph", "cv2", "mediapipe", "faster_whisper"]
    package_status = {name: importlib.util.find_spec(name) is not None for name in packages}
    models = _local_models()
    selected = os.environ.get("VIDEO2STORYBOARD_VLM_MODEL", "").strip()
    return {
        "execution_policy": "local_only",
        "cloud_fallback": "disabled",
        "python": __import__("sys").version.split()[0],
        "packages": package_status,
        "ffmpeg_available": shutil.which("ffmpeg") is not None,
        "lm_studio": models,
        "selected_vlm_model": selected or None,
        "selected_model_listed": bool(selected and selected in models.get("models", [])),
        "ready_for_analysis": all(package_status.values()) and shutil.which("ffmpeg") is not None
            and models.get("reachable", False) and bool(selected and selected in models.get("models", [])),
        "note": "Model listing does not prove vision capability; use a vision-capable model. No media is uploaded by this check.",
    }


@mcp.tool()
def video2storyboard_analyze(
    source_video: str,
    output_dir: str = "outputs",
    frame_interval_seconds: float = 1.0,
    whisper_model: str = "base",
) -> dict[str, Any]:
    """Analyze an explicit local video and write storyboard.json, storyboard.html, and storyboard.svg locally."""
    if frame_interval_seconds <= 0:
        return {"status": "failed", "error": "frame_interval_seconds must be greater than zero"}
    source = Path(source_video).expanduser().resolve()
    if not source.is_file():
        return {"status": "failed", "error": f"Video file not found: {source}"}
    if source.suffix.lower() not in {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}:
        return {"status": "failed", "error": "Unsupported video extension. Use mp4, mov, m4v, webm, avi, or mkv."}
    if not os.environ.get("VIDEO2STORYBOARD_VLM_MODEL", "").strip():
        return {"status": "failed", "error": "VIDEO2STORYBOARD_VLM_MODEL is not set. Configure a local vision-capable LM Studio model."}
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    from video2storyboard.work.storyboard.graph.workflow import app

    result = app.invoke({
        "source_video": str(source),
        "output_dir": str(output),
        "config": {
            "frame_interval_seconds": frame_interval_seconds,
            "whisper_model": whisper_model,
            "vlm_callable": _lm_studio_vlm,
        },
        "errors": [],
    })
    return {
        "status": result.get("status", "unknown"),
        "run_id": result.get("run_id"),
        "source_video": str(source),
        "metadata": result.get("metadata", {}),
        "frame_count": len(result.get("frames", [])),
        "artifacts": result.get("artifacts", {}),
        "errors": result.get("errors", []),
        "execution_policy": "local_only; no cloud fallback",
    }


@mcp.tool()
def video2storyboard_get_run(run_dir: str) -> dict[str, Any]:
    """Inspect an existing local run directory and summarize its storyboard and artifact files."""
    directory = Path(run_dir).expanduser().resolve()
    if not directory.is_dir():
        return {"status": "not_found", "error": f"Run directory not found: {directory}"}
    expected = {
        "json": directory / "storyboard.json",
        "html": directory / "storyboard.html",
        "svg": directory / "storyboard.svg",
    }
    artifacts = {kind: {"path": str(path), "exists": path.is_file(), "bytes": path.stat().st_size if path.is_file() else None}
                 for kind, path in expected.items()}
    summary: dict[str, Any] = {"status": "available" if any(x["exists"] for x in artifacts.values()) else "incomplete",
                               "run_dir": str(directory), "artifacts": artifacts}
    json_path = expected["json"]
    if json_path.is_file():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            summary["run_id"] = data.get("run_id")
            summary["video_id"] = data.get("video_id")
            summary["panel_count"] = len(data.get("panels", []))
            summary["analysis_errors"] = data.get("analysis_errors", [])
        except (OSError, json.JSONDecodeError) as exc:
            summary["json_error"] = str(exc)
            summary["status"] = "invalid_json"
    return summary


if __name__ == "__main__":
    mcp.run(transport="stdio")
