from zoneinfo import ZoneInfo

import pandas as pd
from pandas import DataFrame, Series

from cosimtlk.models import DateTimeLike, FMUInputType
from cosimtlk.simulation.utils import ensure_tz


class ObservationStore:
    def __init__(self) -> None:
        self._db: dict[str, Series] = {}

    @classmethod
    def with_history(cls, **history: Series) -> "ObservationStore":
        store = cls()
        store.store_history(**history)
        return store

    def store_history(self, **history: Series):
        for key, history_ in history.items():
            if not isinstance(history_.index, pd.DatetimeIndex):
                msg = f"The index of the history of '{key}' is not a DatetimeIndex."
                raise ValueError(msg)

            history_.rename_axis("timestamp", inplace=True)
            if history_.index.tz is None:
                history_.index = history_.index.tz_localize(ZoneInfo("UTC"))

            self._db[key] = history_

    def store_observation(self, key: str, value: FMUInputType, ts: DateTimeLike) -> None:
        ts = ensure_tz(ts)
        if key not in self._db:
            self._db[key] = pd.Series(name=key, index=[ts], data=[value]).rename_axis("timestamp")
        self._db[key][ts] = value

    def store_observations(self, ts: DateTimeLike, **values: FMUInputType) -> None:
        for key, value in values.items():
            self.store_observation(key, value, ts)

    def get_observations(
        self,
        key: str,
        start: DateTimeLike | None = None,
        end: DateTimeLike | None = None,
        limit: int | None = None,
    ) -> Series:
        start = ensure_tz(start) if start is not None else None
        end = ensure_tz(end) if end is not None else None

        obs = self._db[key].loc[start:end]
        if limit is not None:
            obs = obs.tail(limit)
        return obs

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self._db)


class ScheduleStore:
    def __init__(self) -> None:
        self._db: dict[str, DataFrame] = {}

    def store_history(self, **history: DataFrame) -> None:
        for key, schedule in history.items():
            if schedule.timestamp.dt.tz is None:
                schedule.timestamp = schedule.timestamp.dt.tz_localize(ZoneInfo("UTC"))

            if schedule.cutoff_date.dt.tz is None:
                schedule.cutoff_date = schedule.cutoff_date.dt.tz_localize(ZoneInfo("UTC"))

            self._db[key] = schedule

    @classmethod
    def with_history(cls, **history: DataFrame) -> "ScheduleStore":
        store = cls()
        store.store_history(**history)
        return store

    @staticmethod
    def _create_schedule_df(schedule: DataFrame, cutoff_date: DateTimeLike) -> DataFrame:
        cutoff_date = ensure_tz(cutoff_date)

        schedule = schedule.copy().rename_axis("timestamp").reset_index().assign(cutoff_date=cutoff_date)
        if schedule.timestamp.dt.tz is None:
            schedule.timestamp = schedule.timestamp.dt.tz_localize(ZoneInfo("UTC"))
        return schedule

    def store_schedule(self, key: str, schedule: DataFrame, cutoff_date: DateTimeLike) -> None:
        schedule = self._create_schedule_df(schedule, cutoff_date)
        if key not in self._db:
            self._db[key] = schedule

        self._db[key] = pd.concat([self._db[key], schedule])

    def store_schedules(self, cutoff_date: DateTimeLike, **schedules: DataFrame) -> None:
        for key, schedule in schedules.items():
            self.store_schedule(key, schedule, cutoff_date)

    def get_schedule(
        self,
        key: str,
        made_after: DateTimeLike | None = None,
        made_before: DateTimeLike | None = None,
    ) -> DataFrame:
        made_after = ensure_tz(made_after) if made_after is not None else None
        made_before = ensure_tz(made_before) if made_before is not None else None

        if made_after is None and made_before is None:
            return self._db[key]

        if made_after is None and made_before is not None:
            mask = self._db[key].index <= made_before
        elif made_after is not None and made_before is None:
            mask = self._db[key].index >= made_after
        else:
            mask = (self._db[key].index >= made_after) & (self._db[key].index <= made_before)
        return self._db[key].loc[mask]

    def get_last_schedule(self, key: str, cutoff_date: DateTimeLike) -> DataFrame:
        cutoff_date = ensure_tz(cutoff_date)
        cutoff_dates = self._db[key]["cutoff_date"].unique()
        last_cutoff_time = cutoff_dates[cutoff_dates <= cutoff_date].max()
        schedule = self.get_schedule(key)
        return schedule.loc[schedule.cutoff_date == last_cutoff_time].set_index("timestamp")
