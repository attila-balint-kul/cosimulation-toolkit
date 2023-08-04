from datetime import datetime

from pydantic import BaseModel

from cosimtlk.models import FMUInputType


class SimulatorModel(BaseModel):
    id: str
    fmu: str
    created_at: datetime


class SimulatorInfoModel(BaseModel):
    name: str
    step_size: int
    current_time: int


class VariableInfoModel(BaseModel):
    description: str | None
    unit: str | None
    type: str | None
    value: FMUInputType | None
    start_value: FMUInputType | None
    min_value: FMUInputType | None
    max_value: FMUInputType | None
    variability: str
