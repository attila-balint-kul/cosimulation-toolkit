from __future__ import annotations

import functools
import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cosimtlk.simulation import Simulator


class EntityLogger(logging.LoggerAdapter):
    def __init__(self, logger, entity):
        self.entity = entity
        self.entity_name = entity.name
        super().__init__(logger, extra={"entity": self.entity_name})

    def log(self, level, msg, *args, **kwargs):
        msg = f"{self.entity.ctx.current_datetime}:{self.entity_name}:{msg}"
        self.logger.log(level, msg, *args, **kwargs)


class Entity(metaclass=ABCMeta):
    def __init__(self, name: str, attributes: dict | None = None) -> None:
        """Entity base class that defines the interface for all entities.

        Abstract base class for all entities in the simulation. An entity is
        a component that can be scheduled in the simulation environment.
        It must implement the `processes` method that returns a list of
        processes that should be scheduled.
        The order of the processes in the list is the order in which they
        will be scheduled in case they should fire exactly the same time.

        Args:
            name: Name of the entity for identification purposes.
            attributes: Dictionary of attributes that can be used to store.
        """
        self._name = name
        self._attributes = attributes or {}
        self._context: Simulator | None = None
        self._logger: EntityLogger | None = None

    def __repr__(self):
        """Representation of the entity."""
        return f"<{self.__class__.__name__}: {self.name}>"

    @property
    def name(self) -> str:
        """Name of the entity."""
        return self._name

    @property
    def attributes(self) -> dict:
        """Attributes of the entity."""
        return self._attributes

    @property
    def ctx(self) -> Simulator:
        """Simulation environment."""
        if self._context is None:
            msg = "Entity has not been initialized yet."
            raise RuntimeError(msg)
        return self._context

    def initialize(self, context: Simulator) -> Entity:
        """Initialize the entity in the simulation.

        Returns:
            List of processes that should be scheduled.
        """
        self._context = context
        self._logger = EntityLogger(context.logger, self)
        return self

    @property
    @abstractmethod
    def processes(self) -> list[Callable[[], Generator]]:
        """List of processes that should be scheduled.

        Returns:
            List of processes.
        """
        raise NotImplementedError

    @functools.cached_property
    def log(self) -> EntityLogger:
        return self._logger

    def wait_for(self, duration: int | float = 0):
        """Wait for a given duration.

        Args:
            duration: Duration to wait for.

        Returns:
            Timeout event.
        """
        return self.ctx.env.timeout(duration)

    def wait_until(self, ts: int | float):
        """Wait until a given timestamp.

        Args:
            ts: Timestamp to wait until.

        Returns:
            Timeout event.
        """
        duration = ts - self.ctx.current_timestamp
        return self.wait_for(duration)


class Source(Entity, metaclass=ABCMeta):
    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [self.generate]

    @abstractmethod
    def interarrival_time(self) -> int | float:
        raise NotImplementedError

    @abstractmethod
    def build_entity(self):
        raise NotImplementedError

    def _generate_interarrival_time(self):
        # if first_creation exists, emit it as the first time, else just use the interarrival_time
        while True:
            yield self.interarrival_time()

    def generate(self):
        for arrival_time in self._generate_interarrival_time():
            timeout = self.wait_for(arrival_time)
            yield timeout
            entity = self.build_entity()
            self.ctx.add_entity(entity)
            self.log.debug(f"created entity={entity} with attributes={entity.attributes}")
