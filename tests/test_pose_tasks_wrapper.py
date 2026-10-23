from pathlib import Path

import pytest

from video2storyboard.pose_tasks import (
    _TasksPose,
    get_landmark_name,
    get_pose_connections,
)


def test_pose_landmark_names_match_media_pipe_contract():
    assert get_landmark_name(0) == "NOSE"
    assert get_landmark_name(32) == "RIGHT_FOOT_INDEX"
    assert get_landmark_name(33) == "LANDMARK_33"


def test_pose_connections_are_integer_pairs():
    connections = list(get_pose_connections())
    assert connections
    assert all(
        isinstance(start, int) and isinstance(end, int)
        for start, end in connections
    )


def test_configured_model_path_is_resolved(monkeypatch, tmp_path: Path):
    model = tmp_path / "model.task"
    model.write_bytes(b"test model")
    monkeypatch.setenv("VIDEO2STORYBOARD_POSE_MODEL", str(model))

    assert _TasksPose._resolve_model_path() == str(model.resolve())


def test_missing_configured_model_fails_clearly(monkeypatch, tmp_path: Path):
    missing = tmp_path / "missing.task"
    monkeypatch.setenv("VIDEO2STORYBOARD_POSE_MODEL", str(missing))

    with pytest.raises(FileNotFoundError, match="VIDEO2STORYBOARD_POSE_MODEL"):
        _TasksPose._resolve_model_path()
