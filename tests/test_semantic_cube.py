"""Tests for Semantic Cube (Issue #21)."""
import sys
import json

sys.path.insert(0, "src")

from video2storyboard.work.dance.semantic_cube import (
    normalize_pose,
    cosine_similarity,
    build_cube_from_poses,
)


def test_normalize_pose_returns_vector():
    lms = [
        {"index": 0, "x": 0.5, "y": 0.5, "z": 0.2, "visibility": 1.0},
        {"index": 1, "x": 0.2, "y": 0.8, "z": 0.3, "visibility": 1.0},
    ]
    v = normalize_pose(lms)
    assert v is not None
    assert len(v) == 6
    assert abs(v[0] - 0.5) < 1e-9
    assert abs(v[3] - 0.2) < 1e-9


def test_normalize_pose_none_on_empty():
    assert normalize_pose([]) is None


def test_cosine_similarity_identical_vectors():
    assert abs(cosine_similarity([1, 0, 0], [1, 0, 0]) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal_vectors():
    assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-9


def test_build_cube_from_poses():
    poses = [
        {
            "frame_id": "f000000",
            "timestamp_seconds": 0.0,
            "status": "detected",
            "landmarks": [
                {"index": i, "x": 0.1 * i, "y": 0.2 * i, "z": 0.0, "visibility": 1.0}
                for i in range(5)
            ],
        },
        {
            "frame_id": "f000001",
            "timestamp_seconds": 1.0,
            "status": "detected",
            "landmarks": [
                {"index": i, "x": 0.1 * i, "y": 0.2 * i, "z": 0.0, "visibility": 1.0}
                for i in range(5)
            ],
        },
    ]
    cube = build_cube_from_poses(poses)
    assert len(cube.samples) == 2
    assert len(cube.similarities) == 1
    # identical poses -> similarity 1.0
    assert abs(cube.similarities[0]["similarity"] - 1.0) < 1e-6
    # html/json serializes without error
    assert "Semantic Cube" in cube.to_html_simple()
    assert '"schema_version": "1.0"' in cube.to_json()
