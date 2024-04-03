import logging
import time
from dataclasses import dataclass, field
from datetime import timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from cosimtlk import FMU
from cosimtlk.simulation import Simulator
from cosimtlk.simulation.entities import FMUEntity, GenericProcess, Input, Measurement, MultiInput, StateObserver
from cosimtlk.simulation.state import SimulationState
from cosimtlk.simulation.storage import ObservationStore
from cosimtlk.simulation.utils import every

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
    fmu_1: FMUState = field(default_factory=FMUState)
    fmu_2: FMUState = field(default_factory=FMUState)


def main():
    fmu = FMU("../../fmus/ModSim.Examples.InputTest.fmu")

    # Entities
    fmu_1_entity = FMUEntity(
        "fmu_1",
        fmu=fmu,
        fmu_step_size=15,
        simulation_step_size=15,
        start_values={
            "integrator.k.": 1,
            "integrator.y_start": 0,
            "bool_setpoint": False,
        },
    )
    fmu_2_entity = FMUEntity(
        "fmu_2",
        fmu=fmu,
        fmu_step_size=15,
        simulation_step_size=15,
        start_values={
            "integrator.k.": 1,
            "integrator.y_start": 0,
            "bool_setpoint": False,
        },
    )

    def set_bool(self):
        self.ctx.state["fmu_1.inputs.bool_setpoint"] = not self.ctx.state["fmu_1.outputs.bool_output"]

    inputs = [
        Input(
            "int_1_input",
            values=pd.Series(
                name="fmu_1.inputs.int_setpoint",
                data=np.random.randint(0, 100, 30),
                index=pd.date_range("2021-01-01T00:00:00", freq="2T", periods=30, tz=ZoneInfo("UTC")),
                dtype=int,
            ),
        ),
        Input(
            "float_1_input",
            values=pd.Series(
                name="fmu_1.inputs.real_setpoint",
                data=np.random.random(20),
                index=pd.date_range("2021-01-01T00:00:00", freq="3T", periods=20, tz=ZoneInfo("UTC")),
                dtype=float,
            ),
        ),
        MultiInput(
            "fmu_2_inputs",
            values=pd.DataFrame(
                index=pd.date_range("2021-01-01T00:00:00", freq="5T", periods=10, tz=ZoneInfo("UTC")),
                data={
                    "fmu_2.inputs.int_setpoint": np.random.randint(10, 100, 10),
                    "fmu_2.inputs.real_setpoint": np.random.random(10) + 5 * 10,
                    "fmu_2.inputs.bool_setpoint": np.random.choice([True, False], 10),
                },
            ),
        ),
        GenericProcess(
            "bool_1_input",
            set_bool,
            scheduler=every(seconds=60),
        ),
    ]

    sensor = StateObserver(
        "sensor",
        measurements=[
            Measurement("fmu_1.inputs.int_setpoint", store_as="int_setpoint_input"),
            Measurement("fmu_1.inputs.real_setpoint", store_as="real_setpoint_input"),
            Measurement("fmu_1.inputs.bool_setpoint", store_as="bool_setpoint_input"),
            Measurement("fmu_1.outputs.int_output"),
            Measurement("fmu_1.outputs.real_output"),
            Measurement("fmu_1.outputs.bool_output"),
            Measurement("fmu_2.inputs.int_setpoint"),
            Measurement("fmu_2.inputs.real_setpoint"),
            Measurement("fmu_2.inputs.bool_setpoint"),
            Measurement("fmu_2.outputs.int_output"),
            Measurement("fmu_2.outputs.real_output"),
            Measurement("fmu_2.outputs.bool_output"),
        ],
        scheduler=every(seconds=60),
    )

    # Simulation
    logger.info(f"Simulation initialization started, {time.time()}")
    simulation = Simulator(
        initial_time=pd.Timestamp("2021-01-01T00:00:00Z"),
        state=State(),
        db=ObservationStore(),
        entities=[
            *inputs,
            fmu_1_entity,
            fmu_2_entity,
            sensor,
        ],
    )
    logger.info(f"Simulation initialization finished, {time.time()}")
    simulation.run_for(timedelta(minutes=20), show_progress_bar=True)
    logger.info(f"Simulation finished, {time.time()}")
    logger.info(simulation.db.to_dataframe().to_string())
    logger.info(f"Simulation results collected, {time.time()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
