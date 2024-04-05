import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
from simpy.util import start_delayed

from cosimtlk.models import DateTimeLike
from cosimtlk.simulation.entities import Entity
from cosimtlk.simulation.environment import Environment
from cosimtlk.simulation.state import SimulationState
from cosimtlk.simulation.utils import ensure_tz


class Simulator:
    def __init__(
        self,
        *,
        initial_time: DateTimeLike,
        state: SimulationState,
        entities: list[Entity] | None = None,
        logger: logging.Logger | None = None,
        **kwargs,
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

        # Set up logger
        self._logger = logger or logging.getLogger(__name__)

        # Create simulation environment
        self._environment = Environment(initial_time=initial_timestamp)
        self._state = state

        # Add entities to the simulation
        self._process_delays = np.arange(0.0005, 0.9995, 0.0005)
        self._entities: dict[str, Entity] = {}
        for entity in entities or []:
            self.add_entity(entity)

        # Set additional attributes
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return f"<Simulator t={self.current_datetime} entities=[{self._entities.keys()}]>"

    def add_entity(self, entity: Entity, delay: int | None = None) -> "Simulator":
        """Add an entity to the simulation.

        Args:
            entity: The entity to add to the simulation.
            delay: Allow the entity to start after a delay.

        Returns:
            The simulator object.
        """
        if entity.name in self._entities:
            msg = f"Entity with name {entity.name} already exists."
            raise ValueError(msg)
        self._entities[entity.name] = entity

        entity.initialize(self)
        for process in entity.processes:
            total_delay = delay or 0 + float(self._process_delays[entity.priority])
            start_delayed(self._environment, process(), total_delay)
        return self

    @property
    def entities(self) -> list[Entity]:
        """The entities inside the simulation."""
        return list(self._entities.values())

    def get_entity(self, name: str) -> Entity:
        """Get an entity by name.

        Args:
            name: The name of the entity to get.

        Returns:
            The entity with the given name.
        """
        return self._entities[name]

    def remove_entity(self, name: str) -> None:
        """Remove an entity from the simulation.

        Args:
            name: The name of the entity to remove.

        Raises:
            KeyError: If the entity does not exist.
        """
        del self._entities[name]

    @property
    def logger(self) -> logging.Logger:
        """The logger for the simulation."""
        return self._logger

    @property
    def state(self) -> SimulationState:
        """The state of the simulation."""
        return self._state

    @property
    def env(self) -> Environment:
        """The simulation environment."""
        return self._environment

    @property
    def current_timestamp(self) -> int:
        """The current simulation time as a unix timestamp."""
        return int(self._environment.now)

    @property
    def current_datetime(self) -> datetime:
        """The current simulation time as a timezone aware datetime object."""
        return datetime.fromtimestamp(self.current_timestamp, tz=self.tzinfo)

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
        self.run(until=self.current_timestamp + duration, show_progress_bar=show_progress_bar)
