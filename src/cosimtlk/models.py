from datetime import datetime
from enum import Enum

from attr import define

FMUInputType = float | int | str | bool


@define
class SimulatorModel:
    id: str
    path: str
    created_at: datetime


@define
class FMUInfo:
    name: str
    step_size: int
    current_time: int


@define
class VariableInfo:
    description: str | None
    value: FMUInputType
    unit: str | None
    type: str | None
    start_value: FMUInputType | None
    min_value: FMUInputType | None
    max_value: FMUInputType | None
    variability: str


class FMUCausaltyType(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    PARAMETER = "parameter"
    CALCULATED_PARAMETER = "calculatedParameter"
    LOCAL = "local"
