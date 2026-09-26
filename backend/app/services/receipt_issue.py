"""回执签发：干算后生成一次性令牌，绑定墙面/卷材编号与卷数，并登记到服务端。"""

import hashlib
import json
import secrets

from app.repositories import receipts as repo


def fingerprint_for(wall: dict, roll: dict) -> str:
    """回执绑定的输入指纹：墙周长/层高与卷材幅宽/长度/花距，确认时据此判断是否已变。"""
    payload = {
        "wall_id": wall["id"],
        "perimeter": wall["perimeter"],
        "height": wall["height"],
        "roll_id": roll["id"],
        "width": roll["width"],
        "length": roll["length"],
        "pattern_cm": roll["pattern_cm"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def issue(wall: dict, roll: dict, calc: dict) -> dict:
    """签发一次性回执：随机令牌 + 输入指纹 + 干算结果快照，服务端登记后返回。"""
    token = secrets.token_urlsafe(24)
    fingerprint = fingerprint_for(wall, roll)
    repo.insert_receipt(token, wall["id"], roll["id"], calc["rolls"], calc, fingerprint)
    return {
        "token": token,
        "wall_id": wall["id"],
        "roll_id": roll["id"],
        "rolls": calc["rolls"],
    }
