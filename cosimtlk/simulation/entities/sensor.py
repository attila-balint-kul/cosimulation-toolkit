from __future__ import annotations

import functools
from typing import Callable, Generator

from cosimtlk.simulation.entities import Entity
from cosimtlk.simulation.storage import ObservationStore, StateStore


class Sensor(Entity):
    def __init__(
        self,
        name: str,
        *,
        measurements: dict[str, str],
        scheduler: Callable,
        state_store: StateStore,
        db: ObservationStore,
    ):
        """An entity that stores the current state of the simulation into long term storage.

        Args:
            name: The name of the entity.
            measurements: A mapping of state names to measurement names. The keys are used as
                the names of the measurements inside the database, while the values determine the state.
            scheduler: A generator function that schedules a function such as `cosimtlk.simulation.utils.every`
                or `cosimtlk.simulation.utils.cron`.
            state_store: The state store to get the state from.
            db: The database to store the observations in.
        """
        super().__init__(name)
        self.measurements = measurements
        self.scheduler = scheduler
        self.state_store = state_store
        self.db = db

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        scheduled_process = self.scheduler(self.__class__.sensing_process)
        return [
            functools.partial(scheduled_process, self),
        ]

    def sensing_process(self):
        values = {
            measurement_name: self.state_store.get(state_name)
            for measurement_name, state_name in self.measurements.items()
        }
        timestamp = self.env.simulation_datetime
        self.db.store_observations(timestamp, **values)
