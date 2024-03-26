from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from cosimtlk._fmu import FMUBase
from cosimtlk.models import FMUInputType
from cosimtlk.simulation.entities import Entity
from cosimtlk.simulation.utils import namespaced

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
        self.fmu = fmu
        self.fmu_instance = None
        self.start_values = start_values
        self.fmu_step_size = fmu_step_size
        self.simulation_step_size = simulation_step_size

        self.namespace = namespace or self.name
        self.input_namespace = namespaced(self.namespace, input_namespace)
        self.output_namespace = namespaced(self.namespace, output_namespace)

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [self.simulation_process]

    def _store_outputs(self, outputs, namespace: str):
        state = {namespaced(namespace, k): v for k, v in outputs.items()}
        self.ctx.state.set(**state)
        self.log.debug(f"outputs={outputs}")

    def initialize(self, context: Simulator) -> FMUEntity:
        super().initialize(context)
        self.fmu_instance = self.fmu.instantiate(
            start_values=self.start_values,
            step_size=self.fmu_step_size,
            start_time=self.ctx.current_timestamp,
        )
        return self

    def simulation_process(self):
        self._store_outputs(self.fmu_instance.read_outputs(), namespace=self.output_namespace)
        while True:
            inputs = self.pre_advance()

            # Advance simulation
            outputs = self.fmu_instance.advance(
                self.ctx.current_timestamp + self.simulation_step_size, input_values=inputs
            )
            yield self.wait_until(self.fmu_instance.current_time)

            self.post_advance(outputs)

    def pre_advance(self) -> dict[str, Any]:
        # Collect inputs
        inputs = asdict(self.ctx.state[self.input_namespace])
        self.log.debug(f"inputs={inputs}")
        return inputs

    def post_advance(self, outputs: dict[str, Any]) -> None:
        # Store outputs
        self._store_outputs(outputs, namespace=self.output_namespace)
