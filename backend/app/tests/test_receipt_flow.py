import os
import sqlite3
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="wallpaper-test-")

from fastapi.testclient import TestClient

from app import seed
from app.config import DB_PATH
from app.main import app

seed.init_db()
client = TestClient(app)


def _runs_count() -> int:
    return len(client.get("/api/runs").json()["items"])


def _dry_run(wall_id=1, roll_id=1):
    r = client.post("/api/estimate/dry-run", json={"wall_id": wall_id, "roll_id": roll_id})
    assert r.status_code == 200, r.text
    return r.json()


def _update(sql, *args):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(sql, args)
        conn.commit()
    finally:
        conn.close()


def test_dry_run_issues_receipt_without_growing_history():
    before = _runs_count()
    body = _dry_run()
    assert body["rolls"] == 11
    receipt = body["receipt"]
    assert receipt["token"] and receipt["wall_id"] == 1 and receipt["roll_id"] == 1
    assert receipt["rolls"] == body["rolls"]
    assert _runs_count() == before


def test_confirm_with_fresh_receipt_writes_one_run():
    before = _runs_count()
    token = _dry_run()["receipt"]["token"]
    r = client.post("/api/estimate/confirm", json={"receipt": token, "note": "ok"})
    assert r.status_code == 200, r.text
    assert r.json()["run_id"] > 0
    assert _runs_count() == before + 1


def test_confirm_missing_or_unknown_receipt_fails():
    before = _runs_count()
    assert client.post("/api/estimate/confirm", json={"receipt": ""}).status_code == 400
    assert client.post("/api/estimate/confirm", json={"receipt": "no-such-token"}).status_code == 404
    assert _runs_count() == before


def test_confirm_reused_receipt_fails():
    before = _runs_count()
    token = _dry_run()["receipt"]["token"]
    assert client.post("/api/estimate/confirm", json={"receipt": token}).status_code == 200
    r = client.post("/api/estimate/confirm", json={"receipt": token})
    assert r.status_code == 409
    assert _runs_count() == before + 1


def test_confirm_fails_when_wall_perimeter_changed():
    before = _runs_count()
    token = _dry_run()["receipt"]["token"]
    _update("UPDATE walls SET perimeter=? WHERE id=?", 17.5, 1)
    try:
        r = client.post("/api/estimate/confirm", json={"receipt": token})
        assert r.status_code == 409
        assert _runs_count() == before
    finally:
        _update("UPDATE walls SET perimeter=? WHERE id=?", 16.0, 1)


def test_confirm_fails_when_roll_changed():
    before = _runs_count()
    token = _dry_run(roll_id=2)["receipt"]["token"]
    _update("UPDATE rolls SET length=? WHERE id=?", 12.0, 2)
    try:
        r = client.post("/api/estimate/confirm", json={"receipt": token})
        assert r.status_code == 409
        assert _runs_count() == before
    finally:
        _update("UPDATE rolls SET length=? WHERE id=?", 10.0, 2)


def test_failed_confirm_can_redry_for_new_receipt():
    before = _runs_count()
    token = _dry_run()["receipt"]["token"]
    _update("UPDATE walls SET perimeter=? WHERE id=?", 18.0, 1)
    try:
        assert client.post("/api/estimate/confirm", json={"receipt": token}).status_code == 409
        # 重新干算拿到新回执（绑定变更后的周长），确认成功且只增一行
        new_token = _dry_run()["receipt"]["token"]
        assert new_token != token
        r = client.post("/api/estimate/confirm", json={"receipt": new_token})
        assert r.status_code == 200, r.text
        assert _runs_count() == before + 1
    finally:
        _update("UPDATE walls SET perimeter=? WHERE id=?", 16.0, 1)


def test_legacy_save_endpoint_removed():
    before = _runs_count()
    r = client.post("/api/estimate", json={"wall_id": 1, "roll_id": 1, "save": True})
    assert r.status_code == 405
    assert _runs_count() == before
