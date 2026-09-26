from fastapi import HTTPException

from app.db import get_conn
from app.engines.wallpaper_math import roll_count
from app.repositories import rolls, walls
from app.services import receipt_issue, receipt_redeem, run_writer


def _load_entities(wall_id: int, roll_id: int):
    wall = walls.get_wall(wall_id)
    if not wall:
        raise HTTPException(404, "wall not found")
    roll = rolls.get_roll(roll_id)
    if not roll:
        raise HTTPException(404, "roll not found")
    if wall.get("data_quality") == "dirty" or roll.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty seed entity")
    return wall, roll


def _calc(wall: dict, roll: dict) -> dict:
    return roll_count(wall["perimeter"], wall["height"], roll["width"], roll["length"], roll["pattern_cm"])


def preview(wall_id: int, roll_id: int):
    """纯试算：不签发回执、不落库。"""
    wall, roll = _load_entities(wall_id, roll_id)
    return {"wall": wall, "roll": roll, **_calc(wall, roll)}


def dry_run(wall_id: int, roll_id: int):
    """干算：算卷数并签发一次性回执，历史表不增行。"""
    wall, roll = _load_entities(wall_id, roll_id)
    calc = _calc(wall, roll)
    receipt = receipt_issue.issue(wall, roll, calc)
    return {"wall": wall, "roll": roll, "receipt": receipt, **calc}


def confirm(token: str, note: str):
    """凭未使用且输入未变的回执，核销并写入一条 run；任一校验失败历史不增行。"""
    if not token:
        raise HTTPException(400, "receipt required")
    with get_conn() as conn:
        receipt = receipt_redeem.load_unused(conn, token)
        wall = walls.get_wall(receipt["wall_id"], conn)
        roll = rolls.get_roll(receipt["roll_id"], conn)
        if not wall or not roll:
            raise HTTPException(409, "wall/roll missing since receipt issued")
        receipt_redeem.assert_matches(receipt, wall, roll)
        receipt_redeem.consume(conn, token)
        run_id = run_writer.write_run(conn, receipt, note)
    return {
        "run_id": run_id,
        "wall_id": receipt["wall_id"],
        "roll_id": receipt["roll_id"],
        "rolls": receipt["rolls"],
    }
