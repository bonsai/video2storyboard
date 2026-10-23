from __future__ import annotations

import json

from video2storyboard.interfaces import mcp as mcp_server


def test_analyze_rejects_missing_video(tmp_path):
    result = mcp_server.video2storyboard_analyze(str(tmp_path / "missing.mp4"))
    assert result["status"] == "failed"
    assert "not found" in result["error"].lower()


def test_analyze_rejects_unsupported_extension(tmp_path):
    source = tmp_path / "not-video.txt"
    source.write_text("not a video", encoding="utf-8")
    result = mcp_server.video2storyboard_analyze(str(source))
    assert result["status"] == "failed"
    assert "unsupported" in result["error"].lower()


def test_get_run_reports_artifacts(tmp_path):
    (tmp_path / "storyboard.json").write_text(
        json.dumps({"run_id": "r1", "video_id": "sample", "panels": [{"panel_id": "p1"}]}),
        encoding="utf-8",
    )
    result = mcp_server.video2storyboard_get_run(str(tmp_path))
    assert result["status"] == "available"
    assert result["run_id"] == "r1"
    assert result["panel_count"] == 1
    assert result["artifacts"]["html"]["exists"] is False


def test_get_run_missing_directory(tmp_path):
    result = mcp_server.video2storyboard_get_run(str(tmp_path / "missing"))
    assert result["status"] == "not_found"
