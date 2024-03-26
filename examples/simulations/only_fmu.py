import logging
from dataclasses import dataclass, field

import pandas as pd

from cosimtlk import FMU
from cosimtlk.simulation import Simulator
from cosimtlk.simulation.entities import FMUEntity
from cosimtlk.simulation.state import SimulationState

logger = logging.getLogger(__name__)


@dataclass
class FMUInputsState:
    int_setpoint: int = field(default=0)
    real_setpoint: float = field(default=0.0)
    bool_setpoint: bool = field(default=False)


@dataclass
class FMUOutputsState:
    int_output: int = field(default=0)
    real_output: float = field(default=0.0)
    bool_output: bool = field(default=False)


@dataclass
class FMUState:
    inputs: FMUInputsState = field(default_factory=FMUInputsState)
    outputs: FMUOutputsState = field(default_factory=FMUOutputsState)


@dataclass
class State(SimulationState):
    fmu: FMUState = field(default_factory=FMUState)


def main():
    fmu_entity = FMUEntity(
        "fmu",
        fmu=FMU("../../fmus/ModSim.Examples.InputTest.fmu"),
        fmu_step_size=60,
        simulation_step_size=60,
        start_values={
            "integrator.k.": 10,
            "integrator.y_start": 0,
            "real_setpoint": 1,
        },
    )

    # Simulation
    simulation = Simulator(
        initial_time=pd.Timestamp("2021-01-01T00:00:00Z"),
        state=State(),
        entities=[
            fmu_entity,
        ],
        logger=logger,
    )
    simulation.run_for(3600, show_progress_bar=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
