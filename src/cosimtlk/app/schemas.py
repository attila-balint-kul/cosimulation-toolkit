from datetime import datetime

from pydantic import BaseModel

from cosimtlk.models import FMUInputType


class SimulatorModel(BaseModel):
    id: str  # noqa: A003
    fmu: str
    created_at: datetime


class SimulatorCreateModel(BaseModel):
    start_values: dict[str, FMUInputType]
    start_time: int
    step_size: int
