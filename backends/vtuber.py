"""VTuber avatar animation backend for Issue #24.

Reads canonical Dance IR and generates Blender keyframes for a VTuber avatar rig.
Maps MediaPipe pose landmarks to a standard VTuber skeleton (head, body, limbs).
Generates NLA actions / F-Curves for expressive motion.
Exports to FBX/GLB or Blender .blend.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from src.video2storyboard.dance_ir import DanceIR, IRPose, IRFrame


# ---------------------------------------------------------------------------
# VTuber avatar bone definitions
# ---------------------------------------------------------------------------

DEFAULT_VTUBER_BONES = (
    # Head & face
    "head_top",       # 頂点
    "head_bottom",    # 首の付け根相当
    # Neck & body
    "neck",           # 頸椎
    "spine",          # 胴体中心
    "spine_r",        # 胴体右
    "spine_l",        # 胴体左
    # Arms
    "shoulder_r",     # 右肩
    "upper_arm_r",    # 右上腕
    "lower_arm_r",    # 右前腕
    "hand_r",         # 右手
    "shoulder_l",     # 左肩
    "upper_arm_l",    # 左上腕
    "lower_arm_l",    # 左前腕
    "hand_l",         # 左手
    # Legs
    "hip_r",          # 右股関節
    "upper_leg_r",    # 右太もも
    "lower_leg_r",    # 右すね
    "foot_r",         # 右足
    "hip_l",          # 左股関節
    "upper_leg_l",    # 左太もも
    "lower_leg_l",    # 左すね
    "foot_l",         # 左足
    # IK helpers
    "ik_hand_r",      # 右手イカー
    "ik_hand_l",      # 左手イカー
    "ik_foot_r",      # 右足イカー
    "ik_foot_l",      # 左足イカー
)


@dataclass
class VTuberRigInfo:
    """Metadata describing a VTuber rig that the animator can consume."""
    name: str = "default_vtuber"
    bones: Sequence[str] = field(default_factory=lambda: DEFAULT_VTUBER_BONES)
    fps: float = 30.0
    armature_name: str = "vtuber_rig"


class VTuberAnimator:
    """Convert Dance IR → Blender keyframes for a VTuber avatar."""

    def __init__(self, rig_info: VTuberRigInfo = None, blend_path: Optional[Path] = None):
        self.rig_info = rig_info or VTuberRigInfo()
        self.blend_path = blend_path
        # bone name → index map (for fast lookup)
        self.bone_index: Dict[str, int] = {
            name: i for i, name in enumerate(self.rig_info.bones)
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def apply(self, ir: DanceIR) -> Dict[str, Any]:
        """Return a dict describing the generated animation assets."""
        keyframes = self._generate_keyframes(ir)
        return {
            "rig_info": self.rig_info,
            "keyframes": keyframes,
            "summary": f"Generated {len(keyframes)} keyframes @ {self.rig_info.fps} fps for {self.rig_info.name}.",
        }

    # ------------------------------------------------------------------
    # Internal: pose → bone transform conversion
    # -------------------------------------------------------------------------
    @staticmethod
    def _normalize(v: Sequence[float]) -> Sequence[float]:
        """L2-normalise a 3‑vector; fall back to (0,0,0)."""
        arr = np.array(v, dtype=float)
        if np.linalg.norm(arr) == 0:
            return 0.0, 0.0, 0.0
        return arr / np.linalg.norm(arr)

    def _landmark_to_bone(self, lm: Dict[str, Any], bones: Sequence[str]) -> Optional[Dict[str, Any]]:
        """Map a single MediaPipe landmark to a VTuber bone pose.

        MediaPipe landmarks referenced from DEFAULT_POSE_LANDMARKS (0‑32).
        We only use a subset that makes sense for a VTuber rig.
        """
        # Rough index → name mapping from MediaPipe
        mp_to_vtuber = {
            0: "head_top",     # NOSE → 頂点 (rough)
            1: "head_bottom",  # NOSE → 首 (rough)
            8: "shoulder_l",   # LEFT_WRIST → rough mapping
            7: "shoulder_r",   # RIGHT_WRIST → rough mapping
            12: "hip_l",       # LEFT_HIP
            11: "hip_r",       # RIGHT_HIP
            24: "foot_l",      # LEFT_FOOT_INDEX
            23: "foot_r",      # RIGHT_FOOT_INDEX
            # Additional rough mappings – these would normally come from
            # a proper rigging definition; for this PoP we keep it simple.
        }

        idx = lm.get("index", -1)
        name = mp_to_vtuber.get(idx)
        if name is None or name not in self.bone_index:
            return None

        x, y, z = lm.get("x", 0), lm.get("y", 0), lm.get("z", 0)
        vis = lm.get("visibility", 1.0)

        # Simple mapping: treat normalized [-1,1] coords as Blender units
        # (they are actually 0‑1 but we stretch to −1…1 for convenience)
        bx = clamp(float(x) * 2.0 - 1.0, -1.0, 1.0)
        by = clamp(float(y) * 2.0 - 1.0, -1.0, 1.0)
        bz = clamp(float(z) * 2.0 - 1.0, -1.0, 1.0)

        return {
            "bone_idx": self.bone_index[name],
            "location": (bx, by, bz),
            "visibility": float(vis),
        }

    # ------------------------------------------------------------------
    # Keyframe generation
    # -------------------------------------------------------------------------
    def _generate_keyframes(self, ir: DanceIR) -> List[Dict[str, Any]]:
        """Turn IR poses into a list of per‑frame keyframe dicts."""
        keyframes: List[Dict[str, Any]] = []
        poses = ir.poses if hasattr(ir, "poses") else ir.get("poses", [])

        for pose_entry in poses:
            # pose_entry could be dict or IRPose – normalise to dict
            if hasattr(pose_entry, "to_dict"):
                pose_dict = pose_entry.to_dict()
            else:
                pose_dict = dict(pose_entry)

            lm_raw = pose_dict.get("landmarks") or []
            # Normalise to list of dicts if a single dict
            if isinstance(lm_raw, dict):
                lm_raw = [lm_raw]

            # Build a name → (x,y,z,vis) map from raw landmarks
            lm_map: Dict[int, Dict[str, float]] = {}
            for lm in lm_raw:
                idx = lm.get("index", -1)
                if idx < 0:
                    continue
                lm_map[idx] = {
                    "x": lm.get("x", 0.0),
                    "y": lm.get("y", 0.0),
                    "z": lm.get("z", 0.0),
                    "visibility": lm.get("visibility", 1.0),
                }

            # Assemble per‑bone data for this frame
            frame_data: Dict[str, Any] = {}
            for bone_name in self.rig_info.bones:
                # Try to find a matching MediaPipe landmark
                mapped = self._landmark_to_bone(lm_map.get(list(lm_map.keys())[0] if lm_map else {}), self.rig_info.bones)
                if mapped is None:
                    # fallback: identity pose
                    mapped = {"bone_idx": self.bone_index.get(bone_name, -1), "location": (0.0, 0.0, 0.0), "visibility": 1.0}
                frame_data[bone_name] = mapped

            # Add frame timestamp
            ts = pose_entry.timestamp_seconds if hasattr(pose_entry, "timestamp_seconds") else pose_entry.get("timestamp_seconds", 0.0)
            frame_data["frame"] = int(ts * self.rig_info.fps)
            frame_data["timestamp"] = ts

            keyframes.append(frame_data)

        return keyframes


def clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main_cli():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="VTuber animator (Issue #24)")
    parser.add_argument("--ir", required=True, help="Path to Dance IR JSON")
    parser.add_argument("--output", default="vtuber_animation", help="Output directory / Blender file name")
    parser.add_argument("--fps", type=float, default=30.0, help="Animation FPS")
    parser.add_argument("--export", choices=["fbx", "blend"], default="blend", help="Export format")
    args = parser.parse_args()

    ir_path = Path(args.ir)
    if not ir_path.is_file():
        print(f"IR file not found: {ir_path}", file=sys.stderr)
        sys.exit(1)

    ir = json.loads(ir_path.read_text(encoding="utf-8"))
    animator = VTuberAnimator()
    result = animator.apply(ir)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Dump a human‑readable JSON summary
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write per‑frame keyframe JSON (consumable by Blender via driver or addon)
    keyframes_path = out_dir / "keyframes.json"
    keyframes_path.write_text(json.dumps(result["keyframes"], indent=2, ensure_ascii=False), encoding="utf-8")

    print(result["summary"])
    print(f"Keyframes written to {keyframes_path}")
    print(f"Summary written to {summary_path}")

    return result


if __name__ == "__main__":
    main_cli()