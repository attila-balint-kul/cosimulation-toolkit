from collections.abc import Iterable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from cosimtlk import FMU
from cosimtlk.simulation.utils import UTC, ensure_tz


@pytest.fixture(scope="session")
def local_fmu():
    fmu = FMU("tests/fixtures/fmus/ModSim.Examples.InputTest.fmu")
    return fmu


@pytest.fixture(scope="function")
def local_fmu_instance(local_fmu):
    instance = local_fmu.instantiate(
        start_time=0,
        step_size=1,
        start_values={},
    )
    yield instance
    instance.close()


def fake_data(
    start: pd.Timestamp = pd.Timestamp("2020-01-01"),  # noqa: B008
    freq: str = "1H",
    periods: int = 10,
    tz: ZoneInfo | None = None,
    columns: Iterable[str] = ("a",),
):
    index = pd.date_range(start, freq=freq, periods=periods, tz=tz)
    data = {column: np.random.random(periods) for column in columns}
    df = pd.DataFrame(index=index, data=data)
    return df


def fake_schedule(
    cutoff_date: pd.Timestamp | Iterable[pd.Timestamp],
    freq: str = "1H",
    periods: int = 10,
    tz: ZoneInfo = UTC,
    columns: Iterable[str] = ("a",),
):
    if isinstance(cutoff_date, pd.Timestamp):
        start = ensure_tz(cutoff_date, default_tz=tz)
        schedule = fake_data(start=start, freq=freq, periods=periods, tz=tz, columns=columns)
        return schedule

    schedules = []
    for made_at_ in cutoff_date:
        start = ensure_tz(made_at_, default_tz=tz)
        schedule_ = (
            fake_data(start=start, freq=freq, periods=periods, tz=tz, columns=columns)
            .rename_axis("timestamp")
            .reset_index()
        )
        schedule_["cutoff_date"] = start
        schedules.append(schedule_)

    schedule = pd.concat(schedules, ignore_index=True)
    return schedule
