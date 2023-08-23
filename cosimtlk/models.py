from datetime import datetime
from enum import Enum
from typing import Union

from pandas import Timestamp

FMUInputType = Union[float, int, str, bool]
DateTimeLike = Union[datetime, Timestamp]


class FMUCausaltyType(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    PARAMETER = "parameter"
    CALCULATED_PARAMETER = "calculatedParameter"
    LOCAL = "local"
