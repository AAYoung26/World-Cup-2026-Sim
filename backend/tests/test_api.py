"""Integration tests for the REST + WebSocket API."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_teams_returns_48():
    resp = client.get("/api/teams")
    assert resp.status_code == 200
    teams = resp.json()
    assert len(teams) == 48
    ids = {t["id"] for t in teams}
    assert len(ids) == 48  # all unique
    assert "ARG" in ids and "BRA" in ids
    for t in teams:
        assert 1400 <= t["elo_rating"] <= 2300
        assert t["group"] in list("ABCDEFGHIJKL")


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_simulate_creates_session():
    resp = client.post("/api/simulate", json={"elo_weight": 80, "num_runs": 200})
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    assert body["ws_url"].startswith("/ws/simulate?session_id=")
    assert body["num_runs"] == 200


def test_results_unknown_session_404():
    resp = client.get("/api/results/does-not-exist")
    assert resp.status_code == 404


def test_websocket_streams_progress_and_completes():
    # Direct WS flow: send params, expect progress messages + a final result.
    with client.websocket_connect("/ws/simulate") as ws:
        ws.send_json({"elo_weight": 100, "num_runs": 200})
        progress = 0
        final = None
        while True:
            msg = ws.receive_json()
            if msg["type"] == "progress":
                progress += 1
                assert msg["total_runs"] == 200
                assert len(msg["top_5_teams"]) <= 5
            elif msg["type"] == "complete":
                final = msg
                break
        assert progress == 4  # 200 runs / 50
        assert final is not None
        assert len(final["teams"]) == 48
        assert final["runs_completed"] == 200


def test_websocket_emits_exactly_20_updates_for_1000_runs():
    with client.websocket_connect("/ws/simulate") as ws:
        ws.send_json({"elo_weight": 100, "num_runs": 1000})
        progress = 0
        while True:
            msg = ws.receive_json()
            if msg["type"] == "progress":
                progress += 1
            elif msg["type"] == "complete":
                break
        assert progress == 20


def test_full_session_flow_with_results_endpoint():
    # POST first, then connect with session_id, then fetch results via REST.
    start = client.post("/api/simulate", json={"elo_weight": 100, "num_runs": 150})
    session_id = start.json()["session_id"]
    ws_url = start.json()["ws_url"]
    with client.websocket_connect(ws_url) as ws:
        while True:
            msg = ws.receive_json()
            if msg["type"] == "complete":
                break
    resp = client.get(f"/api/results/{session_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == session_id
    assert body["runs_completed"] == 150
    assert len(body["teams"]) == 48
