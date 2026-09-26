"""回执核销：确认时校验回执存在、未使用、且签发后墙面/卷材未变，然后原子核销。"""

from fastapi import HTTPException

from app.repositories import receipts as repo
from app.services.receipt_issue import fingerprint_for


def load_unused(conn, token: str) -> dict:
    receipt = repo.get_receipt(token, conn)
    if not receipt:
        raise HTTPException(404, "receipt not found")
    if receipt.get("used_at"):
        raise HTTPException(409, "receipt already used")
    return receipt


def assert_matches(receipt: dict, wall: dict, roll: dict):
    """签发时的墙周长/卷材指纹与当前不一致则拒绝（回执不核销，可重新干算）。"""
    if fingerprint_for(wall, roll) != receipt["fingerprint"]:
        raise HTTPException(409, "wall/roll changed since receipt issued")


def consume(conn, token: str):
    if not repo.consume(conn, token):
        raise HTTPException(409, "receipt already used")
