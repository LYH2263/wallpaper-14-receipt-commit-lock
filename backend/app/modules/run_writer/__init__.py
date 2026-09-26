"""Run writer: the only path that appends a row to calc_runs.

Called with the caller's connection so the run insert commits (or rolls
back) together with the receipt redemption.
"""

import json
from datetime import datetime, timezone


def write_run(conn, wall_id: int, roll_id: int, result: dict, note: str = "") -> int:
    """Insert one calc run and return its id."""
    cur = conn.execute(
        "INSERT INTO calc_runs(wall_id,roll_id,result_json,note,created_at) VALUES (?,?,?,?,?)",
        (
            wall_id,
            roll_id,
            json.dumps(result, ensure_ascii=False),
            note,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    return int(cur.lastrowid)
