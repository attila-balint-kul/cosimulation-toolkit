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
    def __init__(self, name: str, priority: int) -> None:
        """Entity base class that defines the interface for all entities.

        Abstract base class for all entities in the simulation. An entity is
        a component that can be scheduled in the simulation environment.
        It must implement the `processes` method that returns a list of
        processes that should be scheduled.
        The order of the processes in the list is the order in which they
        will be scheduled in case they should fire exactly the same time.

        Args:
            name: Name of the entity for identification purposes.
            priority: Priority of the entity in task scheduling.
        """
        self._name = name
        self._priority = priority
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
    def priority(self) -> int:
        """Priority of the entity in task scheduling."""
        return self._priority

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
