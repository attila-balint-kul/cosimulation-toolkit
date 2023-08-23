from typing import Iterable, Optional, Union
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from cosimtlk.wrappers import FMIWrapper


@pytest.fixture(scope="function")
def wrapper():
    path = "./fmus/ModSim.Layouts.test.fmu"
    return FMIWrapper(path)


def fake_data(
    start: pd.Timestamp = pd.Timestamp("2020-01-01"),
    freq: str = "1H",
    periods: int = 10,
    tz: Optional[ZoneInfo] = None,
    columns: Iterable[str] = ("a",),
):
    index = pd.date_range(start, freq=freq, periods=periods, tz=tz)
    data = {column: np.random.random(periods) for column in columns}
    df = pd.DataFrame(index=index, data=data)
    return df


def fake_schedule(
    made_at: Union[pd.Timestamp, Iterable[pd.Timestamp]],
    freq: str = "1H",
    periods: int = 10,
    tz: Optional[ZoneInfo] = None,
    columns: Iterable[str] = ("a",),
):
    if isinstance(made_at, pd.Timestamp):
        start = made_at + pd.Timedelta(freq)
        schedule = fake_data(start=start, freq=freq, periods=periods, tz=tz, columns=columns)
        return schedule

    schedules = []
    for made_at_ in made_at:
        start = made_at_ + pd.Timedelta(freq)
        schedule_ = (
            fake_data(start=start, freq=freq, periods=periods, tz=tz, columns=columns)
            .rename_axis("timestamp")
            .reset_index()
        )
        schedule_["made_at"] = made_at_.replace(tzinfo=tz)
        schedules.append(schedule_)

    schedule = pd.concat(schedules, ignore_index=True)
    return schedule
