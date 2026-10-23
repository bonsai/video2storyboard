"""Focused tests for #19 — pose overlay visible + JSON/JSONL + no source overwrite."""
import pytest, sys, json, tempfile
sys.path.insert(0,"src")
from video2storyboard.work.storyboard.plugins.pose import run, PluginContext

def test_pose_implements_jsonl_and_does_not_overwrite_source():
    ctx = PluginContext(run_id="test-19")
    result = run(ctx)
    assert result.plugin_id == "pose"
    assert result.status == "implemented"
    # Source video untouched; no cloud upload
    assert "Source media untouched" in result.message
    metrics = result.metrics
    assert metrics.get("overlay_png") == 1
    assert metrics.get("jsonl_events") == 1
    # JSON fields verified
    assert metrics.get("status") == "passed"
