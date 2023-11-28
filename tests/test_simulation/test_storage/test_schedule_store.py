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
        cutoff_date=[
            pd.Timestamp("2021-01-01 00:00:00"),
            pd.Timestamp("2021-01-01 01:00:00"),
        ],
        columns=["a", "b"],
    )
    db.store_history(schedule=history)

    schedule = db.get_schedule("schedule")
    assert isinstance(schedule, pd.DataFrame)
    assert schedule.timestamp.dt.tz == ZoneInfo("UTC")
    assert schedule.cutoff_date.dt.tz == ZoneInfo("UTC")


def test_store_history_with_tz(db):
    history = fake_schedule(
        cutoff_date=[
            pd.Timestamp("2021-01-01 00:00:00"),
            pd.Timestamp("2021-01-01 01:00:00"),
        ],
        columns=["a", "b"],
        tz=ZoneInfo("Europe/Brussels"),
    )
    db.store_history(schedule=history)

    schedule = db.get_schedule("schedule")
    assert isinstance(schedule, pd.DataFrame)
    assert schedule.timestamp.dt.tz == ZoneInfo("Europe/Brussels")
    assert schedule.cutoff_date.dt.tz == ZoneInfo("Europe/Brussels")


def test_get_set_schedule_without_tz(db):
    cutoff_date = pd.Timestamp("2021-01-01 00:00:00")
    schedule = fake_schedule(cutoff_date)

    db.store_schedule("schedule", schedule, cutoff_date=cutoff_date)

    schedule = db.get_schedule("schedule")
    assert isinstance(schedule, pd.DataFrame)
    assert schedule.timestamp.dt.tz == ZoneInfo("UTC")
    assert schedule.cutoff_date.dt.tz == ZoneInfo("UTC")


def test_get_set_schedule_with_tz(db):
    cutoff_date = pd.Timestamp("2021-01-01 00:00:00", tz=ZoneInfo("Europe/Brussels"))
    schedule = fake_schedule(cutoff_date, tz=ZoneInfo("Europe/Brussels"))

    db.store_schedule("schedule", schedule, cutoff_date=cutoff_date)

    schedule = db.get_schedule("schedule")
    assert isinstance(schedule, pd.DataFrame)
    assert schedule.timestamp.dt.tz == ZoneInfo("Europe/Brussels")
    assert schedule.cutoff_date.dt.tz == ZoneInfo("Europe/Brussels")


def test_get_last_schedule(db):
    schedule_1 = fake_schedule(pd.Timestamp("2021-01-01 00:00:00"))
    schedule_2 = fake_schedule(pd.Timestamp("2021-01-01 03:00:00"))
    schedule_3 = fake_schedule(pd.Timestamp("2021-01-01 06:00:00"))
    schedule_4 = fake_schedule(pd.Timestamp("2021-01-01 09:00:00"))

    db.store_schedule("schedule", schedule_1, cutoff_date=pd.Timestamp("2021-01-01 00:00:00"))
    db.store_schedule("schedule", schedule_2, cutoff_date=pd.Timestamp("2021-01-01 03:00:00"))
    db.store_schedule("schedule", schedule_3, cutoff_date=pd.Timestamp("2021-01-01 06:00:00"))
    db.store_schedule("schedule", schedule_4, cutoff_date=pd.Timestamp("2021-01-01 09:00:00"))

    schedule = db.get_last_schedule("schedule", pd.Timestamp("2021-01-01 06:00:00"))
    assert isinstance(schedule, pd.DataFrame)
    assert (schedule.cutoff_date == pd.Timestamp("2021-01-01 06:00:00+00:00")).all()


def test_get_last_schedule_not_exact_time(db):
    schedule_1 = fake_schedule(pd.Timestamp("2021-01-01 00:00:00"))
    schedule_2 = fake_schedule(pd.Timestamp("2021-01-01 03:00:00"))
    schedule_3 = fake_schedule(pd.Timestamp("2021-01-01 06:00:00"))
    schedule_4 = fake_schedule(pd.Timestamp("2021-01-01 09:00:00"))

    db.store_schedule("schedule", schedule_1, cutoff_date=pd.Timestamp("2021-01-01 00:00:00"))
    db.store_schedule("schedule", schedule_2, cutoff_date=pd.Timestamp("2021-01-01 03:00:00"))
    db.store_schedule("schedule", schedule_3, cutoff_date=pd.Timestamp("2021-01-01 06:00:00"))
    db.store_schedule("schedule", schedule_4, cutoff_date=pd.Timestamp("2021-01-01 09:00:00"))

    schedule = db.get_last_schedule("schedule", pd.Timestamp("2021-01-01 08:55:00"))
    assert isinstance(schedule, pd.DataFrame)
    assert (schedule.cutoff_date == pd.Timestamp("2021-01-01 06:00:00+00:00")).all()


if __name__ == "__main__":
    pytest.main()
