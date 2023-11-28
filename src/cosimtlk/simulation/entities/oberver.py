from __future__ import annotations

from abc import ABCMeta
from queue import Empty, Queue
from typing import Protocol

from cosimtlk.simulation.entities import Entity


class Subscriber(Protocol):
    def notify(self, event: dict):
        ...


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list] = {}

    def subscribe(self, event_type: str, subscriber: Subscriber):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(subscriber)

    def publish(self, event_type: str, message: dict) -> None:
        if event_type not in self._subscribers:
            return

        for subscriber in self._subscribers[event_type]:
            subscriber.notify(message)


class Observer(Entity, metaclass=ABCMeta):
    def __init__(self, name: str):
        super().__init__(name)
        self.queue: Queue = Queue()

    def notify(self, message: dict):
        return self.queue.put(message)

    def consume(self) -> dict | None:
        try:
            message = self.queue.get(block=False)
        except Empty:
            message = None
        return message
