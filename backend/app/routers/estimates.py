from fastapi import APIRouter, Query

from app.schemas.estimate import ConfirmRequest, DryRunRequest
from app.services import estimate_service

router = APIRouter()


@router.get("/estimate")
def estimate_preview(wall_id: int = Query(...), roll_id: int = Query(...)):
    """纯试算：只返回卷数，不签发回执、不落库。"""
    return estimate_service.preview(wall_id, roll_id)


@router.post("/estimate/dry-run")
def estimate_dry_run(body: DryRunRequest):
    """干算：返回卷数并签发一次性回执，历史表不增行。"""
    return estimate_service.dry_run(body.wall_id, body.roll_id)


@router.post("/estimate/confirm")
def estimate_confirm(body: ConfirmRequest):
    """确认：凭未使用且输入未变的回执写入一条 run。"""
    return estimate_service.confirm(body.receipt, body.note)
