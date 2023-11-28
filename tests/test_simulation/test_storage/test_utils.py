from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from cosimtlk.simulation.utils import ensure_tz


def test_ensure_tz_timestamp():
    dt = pd.Timestamp("2021-01-01 00:00:00")
    dt = ensure_tz(dt)
    assert dt.tzinfo == ZoneInfo("UTC")


def test_ensure_tz_timestamp_with_tz():
    dt = pd.Timestamp("2021-01-01 00:00:00", tz=ZoneInfo("Europe/Brussels"))
    dt = ensure_tz(dt)
    assert dt.tzinfo == ZoneInfo("Europe/Brussels")


def test_ensure_tz_datetime():
    dt = datetime(2021, 1, 1, 0, 0, 0)  # noqa
    dt = ensure_tz(dt)
    assert dt.tzinfo == ZoneInfo("UTC")


def test_ensure_tz_datetime_with_tz():
    dt = datetime(2021, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("Europe/Brussels"))
    dt = ensure_tz(dt)
    assert dt.tzinfo == ZoneInfo("Europe/Brussels")


if __name__ == "__main__":
    pytest.main()
