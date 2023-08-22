from datetime import datetime
from enum import Enum
from typing import Union, Optional

from pandas import Timestamp
from attr import define

FMUInputType = Union[float, int, str, bool]
DateTimeLike = Union[datetime, Timestamp]


@define
class VariableInfo:
    description: Optional[str]
    value: FMUInputType
    unit: Optional[str]
    type: Optional[str]
    start_value: Optional[FMUInputType]
    min_value: Optional[FMUInputType]
    max_value: Optional[FMUInputType]
    variability: str


class FMUCausaltyType(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    PARAMETER = "parameter"
    CALCULATED_PARAMETER = "calculatedParameter"
    LOCAL = "local"
