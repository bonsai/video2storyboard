"""Typed state shared by the video2storyboard LangGraph workers."""
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class VideoState(TypedDict, total=False):
    source_video: str
    source_id: str
    source_sha256: str
    run_id: str
    output_dir: str
    config: dict[str, Any]
    metadata: dict[str, Any]
    frames: list[dict[str, Any]]
    pose_results: list[dict[str, Any]]
    composition_results: list[dict[str, Any]]
    meaning_results: list[dict[str, Any]]
    transcript_segments: list[dict[str, Any]]
    storyboard: dict[str, Any]
    artifacts: dict[str, str]
    # Parallel workers append their own errors through LangGraph's reducer.
    errors: Annotated[list[dict[str, Any]], operator.add]
    status: str
