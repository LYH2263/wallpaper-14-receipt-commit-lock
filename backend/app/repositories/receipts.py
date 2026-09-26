import json
from datetime import datetime, timezone

from app.db import connect


def insert_receipt(token: str, wall_id: int, roll_id: int, rolls: int, result: dict, fingerprint: str):
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO receipts(token,wall_id,roll_id,rolls,result_json,fingerprint,created_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                token,
                wall_id,
                roll_id,
                rolls,
                json.dumps(result, ensure_ascii=False),
                fingerprint,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_receipt(token: str, conn=None):
    own = conn is None
    conn = conn or connect()
    try:
        row = conn.execute("SELECT * FROM receipts WHERE token=?", (token,)).fetchone()
        return dict(row) if row else None
    finally:
        if own:
            conn.close()


def consume(conn, token: str) -> bool:
    """原子核销：仅当回执未使用时置 used_at，返回是否成功。"""
    cur = conn.execute(
        "UPDATE receipts SET used_at=? WHERE token=? AND used_at IS NULL",
        (datetime.now(timezone.utc).isoformat(), token),
    )
    return cur.rowcount == 1
