from __future__ import annotations

import functools
from collections.abc import Callable, Generator
from dataclasses import dataclass, field

from cosimtlk.simulation.entities import Entity


@dataclass(frozen=True, slots=True)
class Measurement:
    name: str
    store_as: str | None = field(default=None)

    def __post_init__(self):
        object.__setattr__(self, "store_as", self.store_as or self.name)


class StateObserver(Entity):
    def __init__(
        self,
        name: str,
        priority: int,
        *,
        measurements: list[Measurement],
        scheduler: Callable,
    ):
        """An entity that stores the current state of the simulation into long term storage.

        Args:
            name: The name of the entity.
            priority: The priority of the entity in the simulation.
            measurements: A mapping of state names to measurement names. The keys are used as
                the names of the measurements inside the database, while the values determine the state.
            scheduler: A generator function that schedules a function such as `cosimtlk.simulation.utils.every`
                or `cosimtlk.simulation.utils.cron`.
        """
        super().__init__(name, priority)
        self.measurements = measurements
        self.scheduler = scheduler

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        scheduled_process = self.scheduler(self.__class__.sensing_process)
        return [
            functools.partial(scheduled_process, self),
        ]

    def sensing_process(self):
        values = {measurement.store_as: self.ctx.state[measurement.name] for measurement in self.measurements}
        self.log.debug(f"observed measurements={values}")
        self.ctx.db.store_observations(self.ctx.current_datetime, **values)
