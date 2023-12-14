from __future__ import annotations

import logging
from collections.abc import Callable, Generator
from typing import Any, TYPE_CHECKING

from cosimtlk._fmu import FMUBase
from cosimtlk.models import FMUInputType
from cosimtlk.simulation.entities import Entity

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from cosimtlk.simulation import Simulator


class FMUEntity(Entity):
    def __init__(
        self,
        name: str,
        *,
        fmu: FMUBase,
        start_values: dict[str, FMUInputType],
        fmu_step_size: int,
        simulation_step_size: int,
        namespace: str | None = None,
        input_namespace: str = "inputs",
        output_namespace: str = "outputs",
    ):
        super().__init__(name)
        # Simulator inputs
        self.fmu = fmu
        self.fmu_instance = None
        self.start_values = start_values
        self.fmu_step_size = fmu_step_size
        self.simulation_step_size = simulation_step_size

        self.namespace = namespace or self.name
        self.input_namespace = input_namespace
        self.output_namespace = output_namespace

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [self.simulation_process]

    def _store_outputs(self, outputs, namespace: str):
        self.context.state.set(**outputs, namespace=namespace)
        logger.debug(f"{self}: t={self.context.current_datetime}, outputs={outputs}")

    def initialize(self, context: Simulator) -> FMUEntity:
        super().initialize(context)

        self.input_namespace = self.context.state.make_namespace(self.namespace, self.input_namespace)
        self.output_namespace = self.context.state.make_namespace(self.namespace, self.output_namespace)

        self.fmu_instance = self.fmu.instantiate(
            start_values=self.start_values,
            step_size=self.fmu_step_size,
            start_time=self.context.current_timestamp,
        )
        return self

    def simulation_process(self):
        self._store_outputs(self.fmu_instance.read_outputs(), namespace=self.output_namespace)
        while True:
            inputs = self.pre_advance()

            # Advance simulation
            outputs = self.fmu_instance.advance(
                self.context.current_timestamp + self.simulation_step_size, input_values=inputs
            )
            time_until_next_step = self.fmu_instance.current_time - self.context.current_timestamp
            yield self.context.env.timeout(time_until_next_step)

            self.post_advance(outputs)

    def pre_advance(self) -> dict[str, Any]:
        # Collect inputs
        inputs = self.context.state.get_all(namespace=self.input_namespace)
        logger.debug(f"{self}: t={self.context.current_datetime}, inputs={inputs}")
        return inputs

    def post_advance(self, outputs: dict[str, Any]) -> None:
        # Store outputs
        self._store_outputs(outputs, namespace=self.output_namespace)
