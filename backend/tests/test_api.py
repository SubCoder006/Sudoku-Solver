from fastapi.testclient import TestClient

from main import app
from tests.test_solver import EASY, HARD

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"ok": True}


def test_solve_easy():
    r = client.post("/api/solve", json={"grid": EASY, "strategy": "mrv"})
    assert r.status_code == 200
    body = r.json()
    assert body["solvable"] is True
    assert all(v != 0 for row in body["solution"] for v in row)
    assert body["total_steps"] == len(body["steps"])
    assert body["aborted"] is False
    assert body["elapsed_ms"] >= 0


def test_solve_default_strategy_is_mrv():
    r = client.post("/api/solve", json={"grid": EASY})
    assert r.status_code == 200 and r.json()["total_steps"] == 51


def test_solve_conflict_returns_422():
    bad = [row[:] for row in EASY]
    bad[0][2] = 5  # duplicate 5 in row 0
    r = client.post("/api/solve", json={"grid": bad})
    assert r.status_code == 422


def test_solve_bad_shape_returns_422():
    r = client.post("/api/solve", json={"grid": [[0] * 9] * 8})
    assert r.status_code == 422


def test_solve_bad_value_returns_422():
    g = [[0] * 9 for _ in range(9)]
    g[0][0] = 10
    r = client.post("/api/solve", json={"grid": g})
    assert r.status_code == 422


def test_solve_unknown_strategy_returns_422():
    r = client.post("/api/solve", json={"grid": EASY, "strategy": "magic"})
    assert r.status_code == 422


def test_unsolvable_but_valid():
    g = [[0] * 9 for _ in range(9)]
    g[0][:8] = [1, 2, 3, 4, 5, 6, 7, 8]
    g[1][8] = 9
    r = client.post("/api/solve", json={"grid": g})
    assert r.status_code == 200
    body = r.json()
    assert body["solvable"] is False and body["aborted"] is False


def test_validate_reports_conflicts():
    bad = [row[:] for row in EASY]
    bad[0][2] = 5
    r = client.post("/api/validate", json={"grid": bad})
    body = r.json()
    assert body["valid"] is False
    assert [0, 0] in body["conflicts"] and [0, 2] in body["conflicts"]


def test_validate_ok():
    r = client.post("/api/validate", json={"grid": EASY})
    assert r.json() == {"valid": True, "conflicts": []}


def test_compare_hard_matches_benchmark():
    r = client.post("/api/compare", json={"grid": HARD})
    assert r.status_code == 200
    rows = {x["strategy"]: x for x in r.json()["results"]}
    assert rows["naive"]["solvable"] and rows["mrv"]["solvable"]
    assert rows["mrv"]["total_steps"] < rows["naive"]["total_steps"]