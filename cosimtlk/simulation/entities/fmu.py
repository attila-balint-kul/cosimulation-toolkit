from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Generator

from cosimtlk.models import FMUInputType
from cosimtlk.simulation.entities import Entity
from cosimtlk.wrappers import FMIWrapper

if TYPE_CHECKING:
    from cosimtlk.simulation.storage import StateStore

logger = logging.getLogger(__name__)


class FMUEntity(Entity):
    def __init__(
        self,
        name: str,
        *,
        simulator: FMIWrapper,
        start_values: dict[str, FMUInputType],
        step_size: int,
        simulation_step_size: int,
        state_store: StateStore,
        namespace: str | None = None,
        input_namespace: str = "inputs",
        output_namespace: str = "outputs",
    ):
        super().__init__(name)
        # Simulator inputs
        self.simulator = simulator
        self.start_values = start_values
        self.step_size = step_size
        self.simulation_step_size = simulation_step_size

        self.state_store = state_store
        self.namespace = namespace or self.name
        self.input_namespace = self.state_store.make_namespace(self.namespace, input_namespace)
        self.output_namespace = self.state_store.make_namespace(self.namespace, output_namespace)

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [self.simulation_process]

    def _store_outputs(self, outputs):
        self.state_store.set(**outputs, namespace=self.output_namespace)
        logger.debug(f"{self}: t={self.env.simulation_datetime}, outputs={outputs}")

    def simulation_process(self):
        self.simulator.initialize(
            start_values=self.start_values,
            step_size=self.step_size,
            start_time=self.env.simulation_timestamp,
        )
        self._store_outputs(self.simulator.read_outputs())
        while True:
            simulation_timestamp = self.env.simulation_timestamp
            # Collect inputs
            inputs = self.state_store.get_all(namespace=self.input_namespace)
            logger.debug(f"{self}: t={self.env.simulation_datetime}, inputs={inputs}")
            # Advance simulation
            outputs = self.simulator.advance(
                simulation_timestamp + self.simulation_step_size, input_values=inputs
            )
            # Wait until next step
            time_until_next_step = self.simulator.current_time - simulation_timestamp
            yield self.env.timeout(time_until_next_step)
            # Store outputs
            self._store_outputs(outputs)
