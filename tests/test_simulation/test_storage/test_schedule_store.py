from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from cosimtlk.simulation.storage import ScheduleStore
from tests.conftest import fake_schedule


@pytest.fixture(scope="function")
def db():
    return ScheduleStore()


def test_store_history_without_tz(db):
    history = fake_schedule(
        made_at=[pd.Timestamp("2021-01-01 00:00:00"), pd.Timestamp("2021-01-01 01:00:00")],
        columns=["a", "b"],
    )
    db.store_history(schedule=history)

    schedule = db.get_schedule("schedule")
    assert isinstance(schedule, pd.DataFrame)
    assert schedule.timestamp.dt.tz == ZoneInfo("UTC")
    assert schedule.made_at.dt.tz == ZoneInfo("UTC")


def test_store_history_with_tz(db):
    history = fake_schedule(
        made_at=[pd.Timestamp("2021-01-01 00:00:00"), pd.Timestamp("2021-01-01 01:00:00")],
        columns=["a", "b"],
        tz=ZoneInfo("Europe/Brussels"),
    )
    db.store_history(schedule=history)

    schedule = db.get_schedule("schedule")
    assert isinstance(schedule, pd.DataFrame)
    assert schedule.timestamp.dt.tz == ZoneInfo("Europe/Brussels")
    assert schedule.made_at.dt.tz == ZoneInfo("Europe/Brussels")


def test_get_set_schedule_without_tz(db):
    made_at = pd.Timestamp("2021-01-01 00:00:00")
    schedule = fake_schedule(made_at)

    db.store_schedule("schedule", schedule, made_at=made_at)

    schedule = db.get_schedule("schedule")
    assert isinstance(schedule, pd.DataFrame)
    assert schedule.timestamp.dt.tz == ZoneInfo("UTC")
    assert schedule.made_at.dt.tz == ZoneInfo("UTC")


def test_get_set_schedule_with_tz(db):
    made_at = pd.Timestamp("2021-01-01 00:00:00", tz=ZoneInfo("Europe/Brussels"))
    schedule = fake_schedule(made_at, tz=ZoneInfo("Europe/Brussels"))

    db.store_schedule("schedule", schedule, made_at=made_at)

    schedule = db.get_schedule("schedule")
    assert isinstance(schedule, pd.DataFrame)
    assert schedule.timestamp.dt.tz == ZoneInfo("Europe/Brussels")
    assert schedule.made_at.dt.tz == ZoneInfo("Europe/Brussels")
