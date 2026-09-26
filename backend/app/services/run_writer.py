"""写 run：把回执登记时的干算结果快照写入历史表（与核销同事务）。"""

import json

from app.repositories import history


def write_run(conn, receipt: dict, note: str) -> int:
    result = json.loads(receipt["result_json"])
    return history.insert_run(receipt["wall_id"], receipt["roll_id"], result, note, conn=conn)
