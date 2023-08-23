from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from cosimtlk.simulation.storage import ObservationStore
from tests.conftest import fake_data


@pytest.fixture(scope="function")
def db():
    return ObservationStore()


def test_store_history_without_tz(db):
    history = fake_data(columns=["a"])

    db.store_history(a=history.a)

    a = db.get_observations("a")
    assert isinstance(a, pd.Series)
    assert isinstance(a.index, pd.DatetimeIndex)
    assert a.index.name == "timestamp"
    assert a.index.tzinfo == ZoneInfo("UTC")


def test_store_history_with_tz(db):
    history = fake_data(columns=["a"], tz=ZoneInfo("Europe/Brussels"))

    db.store_history(a=history.a)

    a = db.get_observations("a")
    assert isinstance(a, pd.Series)
    assert isinstance(a.index, pd.DatetimeIndex)
    assert a.index.name == "timestamp"
    assert a.index.tzinfo == ZoneInfo("Europe/Brussels")


def test_get_set_observation_without_tz(db):
    db.store_observation("a", 1, datetime.fromisoformat("2021-01-01 00:00:00"))
    db.store_observation("a", 2, pd.Timestamp("2021-01-01 01:00:00"))

    observations = db.get_observations("a")
    assert len(observations) == 2
    assert all(observations.values == [1, 2])
    assert observations.name == "a"
    assert observations.index.name == "timestamp"
    assert observations.index.tzinfo == ZoneInfo("UTC")


def test_get_set_observation_with_tz(db):
    db.store_observation("a", 1, datetime.now(tz=ZoneInfo("Europe/Brussels")))
    db.store_observation("a", 2, pd.Timestamp.now(tz=ZoneInfo("Europe/Brussels")))

    observations = db.get_observations("a")
    assert len(observations) == 2
    assert all(observations.values == [1, 2])
    assert observations.name == "a"
    assert observations.index.name == "timestamp"
    assert observations.index.tzinfo == ZoneInfo("Europe/Brussels")
