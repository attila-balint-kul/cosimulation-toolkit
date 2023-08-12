from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import numpy as np
from simpy.util import start_delayed

from cosimtlk.simulation.environment import Environment
from cosimtlk.simulation.utils import with_tz

if TYPE_CHECKING:
    from cosimtlk.simulation.entities import Entity


class SimulationRunner:

    def __init__(
        self,
        *,
        entities: list[Entity] | None = None,
        initial_time: datetime | int = 0,
        tzinfo: ZoneInfo = ZoneInfo("UTC"),
    ) -> None:
        """Simulation runner.

        Organizes the entities processes into a discrete event simulation. If multiple entities would run at the same
        time, the order is determined by the order of the entities in the entities list.

        Args:
            entities: A list of entities inside the simulation.
            initial_time: The initial time of the simulation. Can be either a datetime or a unix timestamp.
            tzinfo: The timezone of the simulation. If timezone is specified it takes precedence over the tzinfo.
        """
        if isinstance(initial_time, datetime):
            initial_time = with_tz(initial_time)
            tzinfo = initial_time.tzinfo
            initial_time = self._dt_to_timestamp(initial_time)
        self.tzinfo = tzinfo

        # Create simulation environment
        self._environment = Environment(initial_time=initial_time, tzinfo=self.tzinfo)

        # Initialize processes
        processes = []
        for entity in entities or []:
            processes.extend(entity.initialize(self._environment))
        process_delays = np.linspace(0.005, 0.995, len(processes))

        for process, delay in zip(processes, process_delays):
            start_delayed(self._environment, process(), delay)

    def __repr__(self) -> str:
        return f"<SimulationRunner t={self._environment.simulation_timestamp}>"

    @staticmethod
    def _dt_to_timestamp(dt: datetime) -> int:
        """Converts a datetime to a unix timestamp."""
        return int(dt.timestamp())

    @staticmethod
    def _td_to_duration(td: timedelta) -> int:
        """Converts a timedelta to a duration in seconds."""
        return int(td.total_seconds())

    def run(self, until: int | datetime, progress_bar: bool = True):
        """Runs the simulation until the given timestamp.

        Args:
            until: The timestamp until the simulation should run.
            progress_bar: Whether to show a progress bar.
        """
        if isinstance(until, datetime):
            if until.tzinfo is not None and until.tzinfo != self.tzinfo:
                raise ValueError(
                    f"Until must be in the same timezone as the initial time. {self.tzinfo} != {until.tzinfo}")
            until = with_tz(until, tzinfo=self.tzinfo)
            until = self._dt_to_timestamp(until)
        else:
            until = int(until)
        self._environment.run(until=until, progress_bar=progress_bar)

    def run_for(self, duration: int | timedelta, progress_bar: bool = True):
        """Runs the simulation for the given duration.

        Args:
            duration: The duration for which the simulation should run.
            progress_bar: Whether to show a progress bar.
        """
        if isinstance(duration, timedelta):
            duration = self._td_to_duration(duration)
        else:
            duration = int(duration)
        self.run(until=self._environment.simulation_timestamp + duration, progress_bar=progress_bar)
