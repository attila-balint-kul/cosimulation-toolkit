from abc import ABCMeta, abstractmethod
from typing import Callable, Generator

from cosimtlk.simulation.entities import Entity


class Source(Entity, metaclass=ABCMeta):

    def __init__(self, name: str, priority: int):
        """Source base entity that generates entities at a given interarrival time.

        Args:
            name: Name of the source entity.
            priority: Priority of the source entity.
        """
        super().__init__(name, priority)
        self._build_count = 0

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [self.generate]

    @abstractmethod
    def interarrival_time(self) -> int | float:
        raise NotImplementedError

    @abstractmethod
    def build_entity(self):
        raise NotImplementedError

    @property
    def build_count(self) -> int:
        return self._build_count

    def _generate_interarrival_time(self):
        # if first_creation exists, emit it as the first time, else just use the interarrival_time
        while True:
            yield self.interarrival_time()

    def generate(self):
        for arrival_time in self._generate_interarrival_time():
            timeout = self.wait_for(arrival_time)
            yield timeout
            entity = self.build_entity()
            self._build_count += 1
            self.ctx.add_entity(entity)
            self.log.debug(f"created entity={entity} with priority={entity.priority}")
