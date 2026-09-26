import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="wp-receipt-test-")

import pytest
from fastapi import HTTPException

from app import seed
from app.db import connect
from app.services import estimate_service

seed.init_db()


def run_count():
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    finally:
        conn.close()


def update_entity(table, entity_id, **fields):
    conn = connect()
    try:
        for k, v in fields.items():
            conn.execute(f"UPDATE {table} SET {k}=? WHERE id=?", (v, entity_id))
        conn.commit()
    finally:
        conn.close()


def test_dry_run_issues_receipt_without_growing_history():
    before = run_count()
    out = estimate_service.dry_estimate(1, 1)
    assert out["receipt"].startswith("rcpt_")
    assert out["rolls"] == 11
    assert run_count() == before


def test_confirm_writes_one_run_and_burns_receipt():
    before = run_count()
    out = estimate_service.dry_estimate(2, 2)
    res = estimate_service.confirm_estimate(out["receipt"], "ok")
    assert res["run_id"]
    assert run_count() == before + 1

    conn = connect()
    try:
        row = conn.execute("SELECT * FROM calc_runs WHERE id=?", (res["run_id"],)).fetchone()
    finally:
        conn.close()
    assert row["wall_id"] == 2 and row["roll_id"] == 2
    assert '"rolls": 19' in row["result_json"]

    with pytest.raises(HTTPException) as exc:
        estimate_service.confirm_estimate(out["receipt"])
    assert exc.value.status_code == 409
    assert run_count() == before + 1


def test_confirm_missing_or_unknown_receipt_fails():
    before = run_count()
    with pytest.raises(HTTPException) as e1:
        estimate_service.confirm_estimate("")
    assert e1.value.status_code == 400
    with pytest.raises(HTTPException) as e2:
        estimate_service.confirm_estimate("rcpt_nope")
    assert e2.value.status_code == 404
    assert run_count() == before


def test_confirm_fails_when_wall_changed_then_fresh_receipt_works():
    before = run_count()
    out = estimate_service.dry_estimate(1, 1)
    update_entity("walls", 1, perimeter=99.0)
    try:
        with pytest.raises(HTTPException) as exc:
            estimate_service.confirm_estimate(out["receipt"])
        assert exc.value.status_code == 409
        assert run_count() == before

        again = estimate_service.dry_estimate(1, 1)
        assert again["receipt"] != out["receipt"]
        estimate_service.confirm_estimate(again["receipt"])
        assert run_count() == before + 1
    finally:
        update_entity("walls", 1, perimeter=16.0)


def test_confirm_fails_when_roll_changed():
    before = run_count()
    out = estimate_service.dry_estimate(1, 1)
    update_entity("rolls", 1, length=5.0)
    try:
        with pytest.raises(HTTPException) as exc:
            estimate_service.confirm_estimate(out["receipt"])
        assert exc.value.status_code == 409
        assert run_count() == before
    finally:
        update_entity("rolls", 1, length=10.0)
