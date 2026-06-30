"""Tests for mneme-server health endpoint."""

from fastapi.testclient import TestClient

from mneme_server.main import app


def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["tier"] in ("S", "A", "B", "C")


def test_stats():
    with TestClient(app) as client:
        resp = client.get("/stats")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


def test_retain():
    with TestClient(app) as client:
        resp = client.post("/retain", json={"content": "test memory"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


def test_recall():
    with TestClient(app) as client:
        resp = client.post("/recall", json={"query": "test", "top_k": 5})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
