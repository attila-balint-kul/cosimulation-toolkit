from datetime import datetime
from enum import Enum

from pandas import Timestamp

FMUInputType = float | int | str | bool
DateTimeLike = datetime | Timestamp


class FMUCausaltyType(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    PARAMETER = "parameter"
    CALCULATED_PARAMETER = "calculatedParameter"
    LOCAL = "local"
