from types import SimpleNamespace

import pytest

from video2storyboard.work.pose.pose_tasks import (
    _SimpleResult,
    _TasksPose,
    get_landmark_name,
    get_pose_connections,
)


def test_landmark_names_and_integer_connections():
    assert get_landmark_name(0) == "NOSE"
    assert get_landmark_name(32) == "RIGHT_FOOT_INDEX"
    assert get_landmark_name(33) == "LANDMARK_33"
    connections = list(get_pose_connections())
    assert connections
    assert all(isinstance(a, int) and isinstance(b, int) for a, b in connections)


def test_tasks_result_preserves_legacy_landmark_shape():
    point = SimpleNamespace(x=0.1, y=0.2, z=0.3, visibility=0.9)
    result = _SimpleResult(SimpleNamespace(pose_landmarks=[[point]]))
    assert result.pose_landmarks.landmark[0].x == pytest.approx(0.1)
    assert result.pose_landmarks.landmark[0].visibility == pytest.approx(0.9)


def test_configured_model_path_is_resolved_and_validated(tmp_path, monkeypatch):
    model = tmp_path / "model.task"
    model.write_bytes(b"x" * 1_000_001)
    monkeypatch.setenv("VIDEO2STORYBOARD_POSE_MODEL", str(model))
    assert _TasksPose._resolve_model_path() == str(model.resolve())


def test_missing_configured_model_path_fails_clearly(monkeypatch):
    monkeypatch.setenv("VIDEO2STORYBOARD_POSE_MODEL", "/missing/pose.task")
    with pytest.raises(FileNotFoundError, match="VIDEO2STORYBOARD_POSE_MODEL"):
        _TasksPose._resolve_model_path()


def test_small_configured_model_fails_validation(tmp_path, monkeypatch):
    model = tmp_path / "tiny.task"
    model.write_bytes(b"bad")
    monkeypatch.setenv("VIDEO2STORYBOARD_POSE_MODEL", str(model))
    with pytest.raises(ValueError, match="too small"):
        _TasksPose._resolve_model_path()
