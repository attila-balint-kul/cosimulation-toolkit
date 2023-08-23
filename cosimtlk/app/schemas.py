from datetime import datetime

from pydantic import BaseModel

from cosimtlk.models import FMUInputType


class SimulatorModel(BaseModel):
    id: str
    fmu: str
    created_at: datetime


class SimulatorCreateModel(BaseModel):
    start_values: dict[str, FMUInputType] = {}
    start_time: int = 0
    step_size: int = 1
