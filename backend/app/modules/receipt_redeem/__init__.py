"""Receipt redemption: validate and burn one-time receipts, server-side only.

All functions take the caller's connection so redemption happens inside the
same transaction as the run insert. One-time-ness is enforced by the
conditional UPDATE in mark_used, never by any client-side state.
"""

import json
from datetime import datetime, timezone


class ReceiptError(Exception):
    """A receipt cannot be redeemed; carries the HTTP status to report."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def load_receipt(conn, token: str) -> dict:
    """Fetch a receipt by token; fail if missing, unknown or already used."""
    if not token:
        raise ReceiptError(400, "receipt missing")
    row = conn.execute("SELECT * FROM receipts WHERE token=?", (token,)).fetchone()
    if row is None:
        raise ReceiptError(404, "receipt not found")
    receipt = dict(row)
    if receipt["used"]:
        raise ReceiptError(409, "receipt already used")
    receipt["snapshot"] = json.loads(receipt["snapshot_json"])
    receipt["result"] = json.loads(receipt["result_json"])
    return receipt


def assert_snapshot_current(receipt: dict, wall: dict, roll: dict) -> None:
    """Fail if wall/roll calc inputs changed since the receipt was issued."""
    snap = receipt["snapshot"]
    current = {
        "perimeter": wall["perimeter"],
        "height": wall["height"],
        "width": roll["width"],
        "length": roll["length"],
        "pattern_cm": roll["pattern_cm"],
    }
    if any(current[k] != snap[k] for k in current):
        raise ReceiptError(409, "wall or roll changed since receipt issued")


def mark_used(conn, token: str) -> None:
    """Atomically burn the receipt; exactly one concurrent caller can win."""
    cur = conn.execute(
        "UPDATE receipts SET used=1, used_at=? WHERE token=? AND used=0",
        (datetime.now(timezone.utc).isoformat(), token),
    )
    if cur.rowcount != 1:
        raise ReceiptError(409, "receipt already used")
