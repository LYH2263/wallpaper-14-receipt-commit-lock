"""Receipt issuance: server-side registration of one-time dry-run receipts.

A receipt binds the wall id, roll id, the calc-input snapshot and the dry-run
result at issuance time. Issuing a receipt never writes to calc_runs.
"""

import json
import secrets
from datetime import datetime, timezone

from app.db import connect


def issue_receipt(wall_id: int, roll_id: int, snapshot: dict, result: dict) -> str:
    """Register a fresh one-time receipt and return its token."""
    token = "rcpt_" + secrets.token_urlsafe(24)
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO receipts(token,wall_id,roll_id,snapshot_json,result_json,used,created_at)"
            " VALUES (?,?,?,?,?,0,?)",
            (
                token,
                wall_id,
                roll_id,
                json.dumps(snapshot, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return token
    finally:
        conn.close()
