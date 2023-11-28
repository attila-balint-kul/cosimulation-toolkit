from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
from simpy.util import start_delayed

from cosimtlk.models import DateTimeLike
from cosimtlk.simulation.entities import Entity
from cosimtlk.simulation.environment import Environment
from cosimtlk.simulation.storage import ObservationStore, ScheduleStore, StateStore
from cosimtlk.simulation.utils import ensure_tz


class SimulationRunner:
    def __init__(
        self,
        *,
        initial_time: DateTimeLike,
        entities: list[Entity] | None = None,
    ) -> None:
        """Simulation runner.

        Organizes the entities processes into a discrete event simulation. If multiple entities would run at the same
        time, the order is determined by the order of the entities in the entities list.

        Args:
            initial_time: The initial time of the simulation. Can be either a datetime or a Timestamp.
            entities: A list of entities inside the simulation.
        """
        initial_time = self._parse_datetime(initial_time)
        initial_timestamp = self._dt_to_timestamp(initial_time)
        self.tzinfo: ZoneInfo = initial_time.tzinfo

        # Create simulation environment
        self._environment = Environment(initial_time=initial_timestamp, tzinfo=self.tzinfo)

        # Initialize processes
        processes = []
        for entity in entities or []:
            processes.extend(entity.initialize(self._environment))
        process_delays = np.linspace(0.005, 0.995, len(processes))

        for process, delay in zip(processes, process_delays, strict=True):
            start_delayed(self._environment, process(), delay)

    def __repr__(self) -> str:
        return f"<SimulationRunner t={self._environment.current_timestamp}>"

    @property
    def state(self) -> StateStore:
        return self._environment.state

    @property
    def db(self) -> ObservationStore:
        return self._environment.db

    @property
    def schedules(self) -> ScheduleStore:
        return self._environment.schedules

    @staticmethod
    def _parse_datetime(dt: DateTimeLike) -> DateTimeLike:
        return ensure_tz(dt)

    @staticmethod
    def _dt_to_timestamp(dt: DateTimeLike) -> int:
        """Converts a datetime to a unix timestamp."""
        return int(dt.timestamp())

    @staticmethod
    def _td_to_duration(td: timedelta) -> int:
        """Converts a timedelta to a duration in seconds."""
        return int(td.total_seconds())

    def run(self, until: int | datetime, show_progress_bar: bool = True):  # noqa
        """Runs the simulation until the given timestamp.

        Args:
            until: The timestamp until the simulation should run.
            show_progress_bar: Whether to show a progress bar.
        """
        if isinstance(until, datetime):
            if until.tzinfo is not None and until.tzinfo != self.tzinfo:
                msg = f"Until must be in the same timezone as the initial time. {self.tzinfo} != {until.tzinfo}"
                raise ValueError(msg)
            until = ensure_tz(until, default_tz=self.tzinfo)
            until = self._dt_to_timestamp(until)
        else:
            until = int(until)
        self._environment.run(until=until, show_progress_bar=show_progress_bar)

    def run_for(self, duration: int | timedelta, show_progress_bar: bool = True):  # noqa
        """Runs the simulation for the given duration.

        Args:
            duration: The duration for which the simulation should run.
            show_progress_bar: Whether to show a progress bar.
        """
        if isinstance(duration, timedelta):
            duration = self._td_to_duration(duration)
        else:
            duration = int(duration)
        self.run(until=self._environment.current_timestamp + duration, show_progress_bar=show_progress_bar)
