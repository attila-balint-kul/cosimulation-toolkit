from __future__ import annotations

import logging
from collections.abc import Callable, Generator

from cosimtlk._fmu import FMUBase
from cosimtlk.models import FMUInputType
from cosimtlk.simulation.entities import Entity

logger = logging.getLogger(__name__)


class FMUEntity(Entity):
    def __init__(
        self,
        name: str,
        *,
        simulator: FMUBase,
        start_values: dict[str, FMUInputType],
        step_size: int,
        simulation_step_size: int,
        namespace: str | None = None,
        input_namespace: str = "inputs",
        output_namespace: str = "outputs",
    ):
        super().__init__(name)
        # Simulator inputs
        self.fmu = simulator
        self.fmu_instance = None
        self.start_values = start_values
        self.step_size = step_size
        self.simulation_step_size = simulation_step_size

        self.namespace = namespace or self.name
        self.input_namespace = input_namespace
        self.output_namespace = output_namespace

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [self.simulation_process]

    def _store_outputs(self, outputs, namespace: str):
        self.env.state.set(**outputs, namespace=namespace)
        logger.debug(f"{self}: t={self.env.current_datetime}, outputs={outputs}")

    def simulation_process(self):
        input_namespace = self.env.state.make_namespace(self.namespace, self.input_namespace)
        output_namespace = self.env.state.make_namespace(self.namespace, self.output_namespace)

        self.fmu_instance = self.fmu.instantiate(
            start_values=self.start_values,
            step_size=self.step_size,
            start_time=self.env.current_timestamp,
        )
        self._store_outputs(self.fmu_instance.read_outputs(), namespace=output_namespace)
        while True:
            simulation_timestamp = self.env.current_timestamp
            # Collect inputs
            inputs = self.env.state.get_all(namespace=input_namespace)
            logger.debug(f"{self}: t={self.env.current_datetime}, inputs={inputs}")
            # Advance simulation
            outputs = self.fmu_instance.advance(simulation_timestamp + self.simulation_step_size, input_values=inputs)
            # Wait until next step
            time_until_next_step = self.fmu_instance.current_time - simulation_timestamp
            yield self.env.timeout(time_until_next_step)
            # Store outputs
            self._store_outputs(outputs, namespace=output_namespace)
