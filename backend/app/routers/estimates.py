from fastapi import APIRouter, Query
from app.schemas.estimate import ConfirmRequest, EstimateRequest
from app.services import estimate_service

router = APIRouter()


@router.get("/estimate")
def estimate_get(wall_id: int = Query(...), roll_id: int = Query(...)):
    return estimate_service.dry_estimate(wall_id, roll_id)


@router.post("/estimate")
def estimate_post(body: EstimateRequest):
    return estimate_service.dry_estimate(body.wall_id, body.roll_id)


@router.post("/estimate/confirm")
def estimate_confirm(body: ConfirmRequest):
    return estimate_service.confirm_estimate(body.receipt, body.note)
