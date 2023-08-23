from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Callable, Generator, Optional

if TYPE_CHECKING:
    from cosimtlk.simulation import Environment


class Entity(metaclass=ABCMeta):
    def __init__(self, name: str) -> None:
        """Entity base class that defines the interface for all entities.

        Abstract base class for all entities in the simulation. An entity is
        a component that can be scheduled in the simulation environment.
        It must implement the `processes` method that returns a list of
        processes that should be scheduled.
        The order of the processes in the list is the order in which they
        will be scheduled in case they should fire exactly the same time.

        Args:
            name: Name of the entity for identification purposes.
        """
        self._name = name
        self._env: Optional[Environment] = None

    def __repr__(self):
        """Representation of the entity."""
        return f"<{self.__class__.__name__}: {self.name}>"

    @property
    def name(self) -> str:
        """Name of the entity."""
        return self._name

    @property
    def env(self) -> Environment:
        """Simulation environment."""
        return self._env

    def initialize(self, env: Environment) -> list[Callable[[], Generator]]:
        """Initialize the entity in the simulation.

        Returns:
            List of processes that should be scheduled.
        """
        self._env = env
        return self.processes

    @property
    @abstractmethod
    def processes(self) -> list[Callable[[], Generator]]:
        """List of processes that should be scheduled.

        Returns:
            List of processes.
        """
        raise NotImplementedError
