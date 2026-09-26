from fastapi import HTTPException

from app.db import connect
from app.engines.wallpaper_math import roll_count
from app.modules import receipt_issue, receipt_redeem, run_writer
from app.repositories import rolls, walls


def _load_clean_pair(wall_id: int, roll_id: int):
    wall = walls.get_wall(wall_id)
    if not wall:
        raise HTTPException(404, "wall not found")
    roll = rolls.get_roll(roll_id)
    if not roll:
        raise HTTPException(404, "roll not found")
    if wall.get("data_quality") == "dirty" or roll.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty seed entity")
    return wall, roll


def dry_estimate(wall_id: int, roll_id: int):
    """Compute rolls and issue a one-time receipt; history stays untouched."""
    wall, roll = _load_clean_pair(wall_id, roll_id)
    calc = roll_count(
        wall["perimeter"], wall["height"], roll["width"], roll["length"], roll["pattern_cm"]
    )
    snapshot = {
        "perimeter": wall["perimeter"],
        "height": wall["height"],
        "width": roll["width"],
        "length": roll["length"],
        "pattern_cm": roll["pattern_cm"],
    }
    result = {**calc, "wall_id": wall_id, "roll_id": roll_id}
    token = receipt_issue.issue_receipt(wall_id, roll_id, snapshot, result)
    return {"wall": wall, "roll": roll, "receipt": token, **calc}


def confirm_estimate(token: str, note: str = ""):
    """Redeem an unused receipt and write exactly one run.

    Fails (and writes nothing) when the receipt is missing/unknown/used, or
    when the wall or roll changed since the receipt was issued.
    """
    conn = connect()
    try:
        receipt = receipt_redeem.load_receipt(conn, token)
        wall, roll = _load_clean_pair(receipt["wall_id"], receipt["roll_id"])
        receipt_redeem.assert_snapshot_current(receipt, wall, roll)
        receipt_redeem.mark_used(conn, token)
        run_id = run_writer.write_run(
            conn, receipt["wall_id"], receipt["roll_id"], receipt["result"], note
        )
        conn.commit()
        return {"run_id": run_id, "receipt": token, **receipt["result"]}
    except receipt_redeem.ReceiptError as exc:
        conn.rollback()
        raise HTTPException(exc.status_code, exc.detail)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
