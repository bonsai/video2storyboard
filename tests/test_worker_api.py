from fastapi.testclient import TestClient

from video2storyboard import worker_api


def test_health_reports_selected_worker():
    response = TestClient(worker_api.app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == worker_api.WORKER_NAME


def test_run_dispatches_state_to_worker(monkeypatch):
    monkeypatch.setitem(worker_api.WORKERS, "ingest_video", lambda state: {"status": "running", "seen": state["source_video"]})
    monkeypatch.setattr(worker_api, "WORKER_NAME", "ingest_video")
    response = TestClient(worker_api.app).post("/run", json={"state": {"source_video": "/workspace/input/demo.mp4"}})
    assert response.status_code == 200
    assert response.json()["result"]["seen"] == "/workspace/input/demo.mp4"


def test_unknown_worker_returns_service_error(monkeypatch):
    monkeypatch.setattr(worker_api, "WORKER_NAME", "not-a-worker")
    response = TestClient(worker_api.app).post("/run", json={"state": {}})
    assert response.status_code == 500
    assert "Unknown WORKER" in response.json()["detail"]
