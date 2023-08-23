from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd
from pandas import DataFrame, Series

from cosimtlk.models import DateTimeLike, FMUInputType


class StateStore:
    def __init__(self, namespace_separator: str = ":") -> None:
        """A simple state store that allows to store and retrieve values by key and a namespace."""
        if namespace_separator is None or namespace_separator == "":
            raise ValueError("The namespace separator cannot be None or an empty string.")
        assert len(namespace_separator) == 1, "The namespace separator must be a single character."
        self.namespace_separator = namespace_separator
        self._state: dict[str, Any] = {}

    def make_namespace(self, *args: str) -> str:
        return self.namespace_separator.join(args)

    def _slip_namespace(self, item: str) -> list[str]:
        return item.split(self.namespace_separator)

    def __getitem__(self, item: str) -> Any:
        if self.namespace_separator in item:
            current_dict = self._state
            keys = self._slip_namespace(item)
            for key in keys[:-1]:
                current_dict = current_dict.get(key, {})
            return current_dict.get(keys[-1])
        return self._state[item]

    def __setitem__(self, key: str, value: Any) -> None:
        if self.namespace_separator in key:
            current_dict = self._state
            keys = self._slip_namespace(key)
            for key in keys[:-1]:
                current_dict = current_dict.setdefault(key, {})
            current_dict[keys[-1]] = value
        else:
            self._state[key] = value

    def __delitem__(self, key: str) -> None:
        if self.namespace_separator in key:
            current_dict = self._state
            keys = self._slip_namespace(key)
            for key in keys[:-1]:
                current_dict = current_dict.get(key, {})
            current_dict.pop(keys[-1], None)
        else:
            self._state.pop(key, None)

    def get_all(self, *, namespace: Optional[str] = None) -> dict[str, Any]:
        if namespace is None:
            return self._state
        current_dict = self._state
        keys = self._slip_namespace(namespace)
        for key in keys:
            current_dict = current_dict.get(key, {})
        return current_dict

    def get(self, key: str, namespace: Optional[str] = None) -> Any:
        if namespace is not None:
            key = self.make_namespace(namespace, key)
        return self.__getitem__(key)

    def delete(self, *key: str, namespace: Optional[str] = None) -> None:
        if namespace is not None:
            key = [f"{namespace}{self.namespace_separator}{k}" for k in key]
        for k in key:
            del self[k]

    def set(self, namespace: Optional[str] = None, **states: Any) -> None:
        for key, value in states.items():
            if namespace is not None:
                key = f"{namespace}{self.namespace_separator}{key}"
            self[key] = value


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
            assert isinstance(history_.index, pd.DatetimeIndex)

            history_.rename_axis("timestamp", inplace=True)
            if history_.index.tz is None:
                history_.index = history_.index.tz_localize(ZoneInfo("UTC"))

            self._db[key] = history_

    def store_observation(self, key: str, value: FMUInputType, ts: DateTimeLike) -> None:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=ZoneInfo("UTC"))
        if key not in self._db:
            self._db[key] = pd.Series(name=key, index=[ts], data=[value]).rename_axis("timestamp")
        self._db[key][ts] = value

    def store_observations(self, ts: DateTimeLike, **values: FMUInputType) -> None:
        for key, value in values.items():
            self.store_observation(key, value, ts)

    def get_observations(
        self,
        key: str,
        start: Optional[DateTimeLike] = None,
        end: Optional[DateTimeLike] = None,
        limit: Optional[int] = None,
    ) -> Series:
        obs = self._db[key].loc[start:end]
        if limit is not None:
            obs = obs.tail(limit)
        return obs


class ScheduleStore:
    def __init__(self) -> None:
        self._db: dict[str, DataFrame] = {}

    def store_history(self, **history: DataFrame) -> None:
        for key, schedule in history.items():
            if schedule.timestamp.dt.tz is None:
                schedule.timestamp = schedule.timestamp.dt.tz_localize(ZoneInfo("UTC"))

            if schedule.made_at.dt.tz is None:
                schedule.made_at = schedule.made_at.dt.tz_localize(ZoneInfo("UTC"))

            self._db[key] = schedule

    @classmethod
    def with_history(cls, **history: DataFrame) -> "ScheduleStore":
        store = cls()
        store.store_history(**history)
        return store

    @staticmethod
    def _create_schedule_df(schedule: DataFrame, made_at: DateTimeLike) -> DataFrame:
        if made_at.tzinfo is None:
            made_at = made_at.replace(tzinfo=ZoneInfo("UTC"))

        schedule = schedule.copy().rename_axis("timestamp").reset_index().assign(made_at=made_at)
        if schedule.timestamp.dt.tz is None:
            schedule.timestamp = schedule.timestamp.dt.tz_localize(ZoneInfo("UTC"))
        return schedule

    def store_schedule(self, key: str, schedule: DataFrame, made_at: DateTimeLike) -> None:
        schedule = self._create_schedule_df(schedule, made_at)

        if key not in self._db:
            self._db[key] = schedule

        self._db[key] = pd.concat([self._db[key], schedule])

    def store_schedules(self, made_at: DateTimeLike, **schedules: DataFrame) -> None:
        for key, schedule in schedules.items():
            self.store_schedule(key, schedule, made_at)

    def get_schedule(
        self,
        key: str,
        made_after: Optional[DateTimeLike] = None,
        made_before: Optional[DateTimeLike] = None,
    ) -> DataFrame:
        if made_after is None and made_before is None:
            return self._db[key]

        if made_after is None and made_before is not None:
            mask = self._db[key].index <= made_before
        elif made_after is not None and made_before is None:
            mask = self._db[key].index >= made_after
        else:
            mask = (self._db[key].index >= made_after) & (self._db[key].index <= made_before)
        return self._db[key].loc[mask]

    def get_last_schedule(self, key: str, made_at: DateTimeLike) -> FMUInputType:
        last_made_at = (self._db[key]["made_at"].unique() <= made_at).max()
        return self._db[key].loc["made_at" == last_made_at, key]
