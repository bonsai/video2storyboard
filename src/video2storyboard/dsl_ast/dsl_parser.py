"""Typed AST nodes for DSL (Issue #25).

Validates input schema before transformation to IR.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml


@dataclass
class DSLNode:
    """Base AST node for DSL elements."""
    kind: str
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DSLInterval:
    start_seconds: float
    end_seconds: float


@dataclass
class DSLTransform:
    source_joint_space: str = "mediapipe"
    target_space: str = "blender_armature"
    smoothing: str = "linear"


@dataclass
class DSLOutput:
    format: str = "ir_json"
    version: str = "1.0"
    artifacts: List[str] = field(default_factory=list)


@dataclass
class DSLConfig:
    dsl_version: str = "1.0"
    name: str = ""
    interval: DSLInterval = field(default_factory=lambda: DSLInterval(0.0, 0.0))
    source_video: Optional[str] = None
    frame_interval_seconds: float = 1.0
    pose: Dict[str, Any] = field(default_factory=dict)
    transform: DSLTransform = field(default_factory=DSLTransform)
    rig: Dict[str, Any] = field(default_factory=dict)
    output: DSLOutput = field(default_factory=DSLOutput)


def parse_dsl(path: str | Path) -> DSLConfig:
    """Parse YAML DSL into validated AST (DSLConfig)."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("DSL must be a YAML mapping")

    # Validate required fields
    if "dsl_version" not in data:
        raise ValueError("DSL missing required field: dsl_version")
    if data.get("dsl_version") != "1.0":
        raise ValueError(f"Unsupported DSL version: {data.get('dsl_version')}")

    interval_data = data.get("interval", {})
    interval = DSLInterval(
        start_seconds=float(interval_data.get("start_seconds", 0.0)),
        end_seconds=float(interval_data.get("end_seconds", 0.0)),
    )
    if interval.start_seconds < 0 or interval.end_seconds < interval.start_seconds:
        raise ValueError("Invalid interval: start must be >= 0 and <= end")

    pose_data = data.get("pose", {})
    rig_data = data.get("rig", {})
    transform_data = data.get("transform", {})
    output_data = data.get("output", {})

    # Validate rig joint order has major joints
    joint_order = rig_data.get("joint_order", [])
    if not joint_order or len(joint_order) < 5:
        raise ValueError("Rig joint_order must include at least 5 joints")

    config = DSLConfig(
        dsl_version=str(data.get("dsl_version")),
        name=str(data.get("name", "")),
        interval=interval,
        source_video=data.get("source_video"),
        frame_interval_seconds=float(data.get("frame_interval_seconds", 1.0)),
        pose=pose_data,
        transform=DSLTransform(
            source_joint_space=str(transform_data.get("source_joint_space", "mediapipe")),
            target_space=str(transform_data.get("target_space", "blender_armature")),
            smoothing=str(transform_data.get("smoothing", "linear")),
        ),
        rig=rig_data,
        output=DSLOutput(
            format=str(output_data.get("format", "ir_json")),
            version=str(output_data.get("version", "1.0")),
            artifacts=list(output_data.get("artifacts", [])),
        ),
    )
    return config


def ast_to_ir(ast: DSLConfig, source_video_path: str = "", source_sha256: str = "") -> "DanceIR":
    """Convert validated AST to canonical IR (using dance_ir module)."""
    from src.video2storyboard.dance_ir import DanceIR
    ir = DanceIR(
        source_video=source_video_path,
        source_sha256=source_sha256,
        interval={"start_seconds": ast.interval.start_seconds,
                  "end_seconds": ast.interval.end_seconds},
    )
    ir.metadata["dsl_version"] = ast.dsl_version
    ir.metadata["dsl_name"] = ast.name
    ir.metadata["frame_interval_seconds"] = ast.frame_interval_seconds
    ir.metadata["joint_order"] = ast.rig.get("joint_order", [])
    return ir
