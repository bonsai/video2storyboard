"""HTTP worker microservice for one video2storyboard graph node.

Set WORKER to an allowlisted node name. Each container exposes POST /run and GET /health.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from video2storyboard.work.storyboard.graph import nodes

WORKERS = {
    "ingest_video": nodes.ingest_video,
    "video2png": nodes.video2png,
    "eye_pose_mp": nodes.eye_pose_mp,
    "eye_composition_cv2": nodes.eye_composition_cv2,
    "eye_meaning_vlm": nodes.eye_meaning_vlm,
    "ear_stt_whisper": nodes.ear_stt_whisper,
    "hand_storyboard_builder": nodes.hand_storyboard_builder,
    "paper_html_svg": nodes.paper_html_svg,
    "validate_storyboard": nodes.validate_storyboard,
}
WORKER_NAME = os.environ.get("WORKER", "ingest_video")
app = FastAPI(title=f"video2storyboard:{WORKER_NAME}", version="1.0.0")


class WorkerRequest(BaseModel):
    state: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": WORKER_NAME}


@app.post("/run")
def run_worker(request: WorkerRequest) -> dict[str, Any]:
    worker = WORKERS.get(WORKER_NAME)
    if worker is None:
        raise HTTPException(status_code=500, detail=f"Unknown WORKER: {WORKER_NAME}")
    state = dict(request.state)
    if WORKER_NAME == "eye_meaning_vlm":
        # Adapter stays local and uses the configured LM Studio endpoint only.
        from video2storyboard.interfaces.mcp import _lm_studio_vlm
        state.setdefault("config", {})
        state["config"] = {**state["config"], "vlm_callable": _lm_studio_vlm}
    try:
        result = worker(state)
        return {"service": WORKER_NAME, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"{WORKER_NAME} failed: {type(exc).__name__}: {exc}") from exc
