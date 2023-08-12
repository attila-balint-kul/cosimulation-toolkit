from typing import Callable, Generator

from cosimtlk.simulation import SimulationRunner
from cosimtlk.simulation.storage import StateStore
from cosimtlk.simulation.entities import Entity, FMUEntity
from cosimtlk.simulation.utils import every, cron
from cosimtlk.simulators import FMUSimulator


class ReaderEntity(Entity):

    def __init__(self, name: str, state_store: StateStore):
        super().__init__(name)
        self.state_store = state_store

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [
            self.print_process,
        ]

    @cron(minute="*", hour="*", day="*", month="*", weekday="*")
    def print_process(self):
        print(f"{self}: t={self.env.simulation_timestamp}, state={self.state_store.get_all()}")


class WriterEntity(Entity):

    def __init__(self, name: str, state_store: StateStore):
        super().__init__(name)
        self.state_store = state_store
        self.int_input = 0
        self.float_input = 0.0
        self.bool_input = False

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [
            self.int_process,
            self.float_process,
            self.bool_process,
        ]

    @cron(minute="*/2")
    def int_process(self):
        self.state_store.set(input_int=self.int_input, namespace="C:inputs")
        self.int_input += 1

    @cron(minute="*/3")
    def float_process(self):
        self.state_store.set(input_float=self.float_input, namespace="C:inputs")
        self.float_input += 1.1

    @cron(minute="*/5")
    def bool_process(self):
        self.state_store.set(input_bool=self.bool_input, namespace="C:inputs")
        self.bool_input = not self.bool_input


def main():
    fmu = FMUSimulator("./fmus/RealBoolIntTest.fmu", step_size=15)
    state_store = StateStore()
    simulation = SimulationRunner(
        entities=[
            WriterEntity("B", state_store=state_store),
            FMUEntity("C", simulator=fmu, state_store=state_store),
            ReaderEntity("A", state_store=state_store),
        ],
    )
    simulation.run_for(7200, progress_bar=False)


if __name__ == '__main__':
    main()
