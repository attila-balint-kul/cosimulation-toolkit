from __future__ import annotations

import functools
from collections.abc import Callable, Generator

from cosimtlk.simulation.entities import Entity


class StateObserver(Entity):
    def __init__(
        self,
        name: str,
        *,
        measurements: list[str],
        scheduler: Callable,
    ):
        """An entity that stores the current state of the simulation into long term storage.

        Args:
            name: The name of the entity.
            measurements: A mapping of state names to measurement names. The keys are used as
                the names of the measurements inside the database, while the values determine the state.
            scheduler: A generator function that schedules a function such as `cosimtlk.simulation.utils.every`
                or `cosimtlk.simulation.utils.cron`.
        """
        super().__init__(name)
        self.measurements = measurements
        self.scheduler = scheduler

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        scheduled_process = self.scheduler(self.__class__.sensing_process)
        return [
            functools.partial(scheduled_process, self),
        ]

    def sensing_process(self):
        values = {measurement: self.env.state.get(measurement) for measurement in self.measurements}
        timestamp = self.env.current_datetime
        self.env.db.store_observations(timestamp, **values)
