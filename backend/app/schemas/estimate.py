from pydantic import BaseModel


class EstimateRequest(BaseModel):
    wall_id: int
    roll_id: int


class ConfirmRequest(BaseModel):
    receipt: str
    note: str = ""
