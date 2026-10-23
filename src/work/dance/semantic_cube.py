"""Semantic Cube visualization for dance similarity (Issue #21).

Builds feature vectors from MediaPipe pose landmarks and computes
pairwise cosine similarity, producing JSON + simple HTML.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

FEATURE_AXES = ("posture", "movement", "intensity")


def normalize_pose(landmarks: List[Dict[str, Any]]) -> Optional[List[float]]:
    """MediaPipe pose landmarks を float ベクトルに正規化。"""
    if not landmarks:
        return None
    vec: List[float] = []
    for lm in landmarks:
        vis = float(lm.get("visibility", 1.0))
        x = float(lm.get("x", 0.0))
        y = float(lm.get("y", 0.0))
        z = float(lm.get("z", 0.0))
        vec.extend([vis * x, vis * y, vis * z])
    # trailing zeros remove
    while vec and abs(vec[-1]) < 1e-9:
        vec.pop()
    return vec if vec else None


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    arr_a = np.array(a, dtype=float)
    arr_b = np.array(b, dtype=float)
    if arr_a.size == 0 or arr_b.size == 0:
        return 0.0
    na, nb = np.linalg.norm(arr_a), np.linalg.norm(arr_b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (na * nb))


@dataclass
class SemanticCube:
    """Semantic Cube (v1.0) — 類似度可視化用データ構造。"""
    name: str = "semantic-cube"
    axes: List[str] = field(default_factory=lambda: list(FEATURE_AXES))
    samples: List[Dict[str, Any]] = field(default_factory=list)
    similarities: List[Dict[str, Any]] = field(default_factory=list)

    def add_sample(self, sample_id: str, timestamp: float, vector: Sequence[float],
                   source: str = "real") -> None:
        self.samples.append({
            "id": sample_id,
            "timestamp": timestamp,
            "vector": list(vector) if vector else [],
            "source": source,
        })

    def add_similarity(self, a_id: str, b_id: str, sim: float) -> None:
        self.similarities.append({
            "sample_a": a_id,
            "sample_b": b_id,
            "similarity": round(sim, 4),
        })

    def build(self) -> None:
        n = len(self.samples)
        for i in range(n):
            for j in range(i + 1, n):
                a = self.samples[i].get("vector", [])
                b = self.samples[j].get("vector", [])
                sim = cosine_similarity(a, b)
                self.add_similarity(self.samples[i]["id"], self.samples[j]["id"], sim)

    def to_json(self) -> str:
        return json.dumps({
            "schema_version": "1.0",
            "name": self.name,
            "axes": self.axes,
            "samples": self.samples,
            "similarities": self.similarities,
        }, indent=2, ensure_ascii=False)

    def to_html_simple(self) -> str:
        sample_rows = []
        for s in self.samples:
            v = ",".join(f"{v:.4f}" for v in s.get("vector", []))
            sample_rows.append(
                f'<tr><td>{s["id"]}</td><td>{s["source"]}</td>'
                f'<td>{s["timestamp"]:.2f}</td><td>{v}</td></tr>'
            )
        sim_rows = []
        for s in self.similarities:
            sim_rows.append(
                f'<tr><td>{s["sample_a"]}</td><td>{s["sample_b"]}</td>'
                f'<td>{s["similarity"]:.4f}</td></tr>'
            )
        return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><title>Semantic Cube</title></head>
<body><h1>Semantic Cube — Dance Similarity</h1>
<table border="1"><tr><th>sample</th><th>source</th><th>timestamp</th><th>vector</th></tr>
{"".join(sample_rows)}</tbody></table>
<h2>Similarities</h2><table border="1"><tr><th>sample a</th><th>sample b</th><th>similarity</th></tr>
{"".join(sim_rows)}</tbody></table></body></html>"""


def build_cube_from_poses(poses: Sequence[Dict[str, Any]]) -> SemanticCube:
    """Dance pose dicts から SemanticCube を構築。"""
    cube = SemanticCube()
    seen_ids: set = set()
    for i, pr in enumerate(poses or []):
        fid = pr.get("frame_id")
        if not fid or fid in seen_ids:
            continue
        seen_ids.add(fid)
        lm = pr.get("landmarks") or []
        vec = normalize_pose(lm)
        if vec is None:
            continue
        source = "real" if pr.get("status") == "detected" else "real"
        cube.add_sample(fid, float(pr.get("timestamp_seconds", 0.0)), vec, source)
    cube.build()
    return cube


def build_cube_from_pose_results(pose_results: Sequence[Dict[str, Any]]) -> SemanticCube:
    return build_cube_from_poses(pose_results)


def main_cli():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Semantic Cube builder")
    parser.add_argument("--pose-results", required=True, help="pose_results.json path")
    parser.add_argument("--output-dir", default="outputs/semantic_cube")
    args = parser.parse_args()
    with open(args.pose_results) as f:
        pr = json.load(f)
    cube = build_cube_from_poses(pr.get("results", []))
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "cube.json").write_text(cube.to_json(), encoding="utf-8")
    (out / "cube.html").write_text(cube.to_html_simple(), encoding="utf-8")
    print(f"Built Semantic Cube: {len(cube.samples)} samples, {len(cube.similarities)} similarities")
    print(f"HTML: {out}/cube.html")
    print(f"JSON: {out}/cube.json")


if __name__ == "__main__":
    main_cli()