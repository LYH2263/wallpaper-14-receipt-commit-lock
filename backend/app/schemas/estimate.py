from pydantic import BaseModel


class DryRunRequest(BaseModel):
    wall_id: int
    roll_id: int


class ConfirmRequest(BaseModel):
    receipt: str
    note: str = ""
