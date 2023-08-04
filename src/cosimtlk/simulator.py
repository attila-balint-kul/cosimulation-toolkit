from __future__ import annotations

import logging
import shutil
from uuid import uuid4
from datetime import timedelta
from pathlib import Path

import fmpy
from fmpy.fmi2 import FMU2Slave
from fmpy.model_description import ModelDescription, ScalarVariable

from cosimtlk.models import FMUInfo, VariableInfo, FMUCausaltyType, FMUInputType

logger = logging.getLogger(__name__)


class FMUSimulator:
    def __init__(
        self,
        path: Path | str,
        step_size: int | timedelta = 1,
        init_values: dict[str, FMUInputType] | None = None,
        output_names: list[str] | None = None,
    ):
        """Simulator using an FMU.

        Args:
            path: Path of the FMU file.
            step_size: FMU simulation step size.
            init_values: Initial values for the inputs.
            output_names: Names of the outputs to be returned. If None, all outputs are returned.
        """
        # Path to the FMU file
        fmu_path = Path(path).resolve()
        if not fmu_path.exists():
            raise FileNotFoundError(f"FMU file not found: {fmu_path}")
        if not fmu_path.suffix == ".fmu":
            raise ValueError(f"FMU file must have .fmu extension: {fmu_path}")
        self.fmu_path = str(fmu_path)

        # Read model description from the FMU
        self.model_description: ModelDescription = fmpy.read_model_description(self.fmu_path)

        # Create input and output maps
        self._inputs: dict[str, ScalarVariable] = {
            variable.name: variable
            for variable in self.model_description.modelVariables
            if variable.causality == FMUCausaltyType.INPUT
        }
        self._outputs: dict[str, ScalarVariable] = {
            variable.name: variable
            for variable in self.model_description.modelVariables
            if variable.causality == FMUCausaltyType.OUTPUT
        }

        # Create FMU slave
        if not self._check_current_platform_is_supported():
            logger.warning(f"{fmpy.platform} is not supported by this FMU, recompiling...")
            fmpy.util.compile_platform_binary(self.fmu_path)
            logger.info(f"Recompiled FMU for platform {fmpy.platform}.")

        self._unzipdir = fmpy.extract(self.fmu_path)
        self.fmu = FMU2Slave(
            unzipDirectory=self._unzipdir,
            guid=self.model_description.guid,
            instanceName=f"{uuid4()}",
            modelIdentifier=self.model_description.coSimulation.modelIdentifier,
        )
        self._instantiated = False
        self.fmu.instantiate(visible=False, callbacks=None, loggingOn=False)
        self._instantiated = True

        # Step size in seconds
        self._current_time = 0
        self._step_size = 0  # reset will set the step size
        self._interested_outputs = output_names
        self.reset(step_size, init_values, output_names)

    def _check_current_platform_is_supported(self) -> bool:
        current_platform = fmpy.platform
        supported_platforms = fmpy.supported_platforms(self.fmu_path)
        return current_platform in supported_platforms

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(t={self._current_time}, path={self.fmu_path!r})"

    def __str__(self) -> str:
        return f"FMU({self.model_description.modelName})"

    def __enter__(self) -> FMUSimulator:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        if not self._instantiated:
            return

        self.fmu.terminate()
        self.fmu.freeInstance()
        self._instantiated = False
        shutil.rmtree(self._unzipdir, ignore_errors=True)

    def reset(
        self,
        step_size: int | timedelta = 1,
        init_values: dict[str, FMUInputType] | None = None,
        output_names: list[str] | None = None,
    ) -> None:
        self._check_instantiated()

        # Set step size
        if isinstance(step_size, timedelta):
            step_size = int(step_size.total_seconds())
        self._step_size = step_size

        self._interested_outputs = output_names
        self._initialize_fmu(init_values, current_time=0)

    def _check_instantiated(self):
        if not self._instantiated:
            raise RuntimeError("FMU is not instantiated.")

    def _initialize_fmu(
        self,
        init_values: dict[str, FMUInputType] | None = None,
        current_time: int = 0,
    ):
        self._output_names = {
            "Real": [],
            "Integer": [],
            "Boolean": [],
            "String": [],
        }
        self._output_refs = {
            "Real": [],
            "Integer": [],
            "Boolean": [],
            "String": [],
        }

        interested_outputs = self._interested_outputs or list(self._outputs.keys())
        for variable in self.model_description.modelVariables:
            if (
                variable.causality == FMUCausaltyType.OUTPUT
                and variable.name in interested_outputs
            ):
                self._output_names[variable.type].append(variable.name)
                self._output_refs[variable.type].append(variable.valueReference)

        # Initialize FMU
        self._current_time = current_time
        self.fmu.reset()
        self.fmu.setupExperiment(startTime=self._current_time)

        self.fmu.enterInitializationMode()
        init_values = init_values or {}
        fmpy.simulation.apply_start_values(
            self.fmu, self.model_description, start_values=init_values
        )
        self.fmu.exitInitializationMode()

    def info(self) -> FMUInfo:
        return FMUInfo(
            name=self.model_description.modelName,
            step_size=self._step_size,
            current_time=self._current_time,
        )

    def inputs(self) -> dict[str, VariableInfo]:
        return {
            i.name: VariableInfo(
                type=i.type,
                description=i.description,
                unit=i.unit,
                value=self._read_variable(i),
                min_value=i.min,
                max_value=i.max,
                start_value=i.start,
                variability=i.variability,
            )
            for i in self._inputs.values()
        }

    def outputs(self) -> dict[str, VariableInfo]:
        return {
            o.name: VariableInfo(
                type=o.type,
                description=o.description,
                unit=o.unit,
                value=self._read_variable(o),
                min_value=o.min,
                max_value=o.max,
                start_value=o.start,
                variability=o.variability,
            )
            for o in self._outputs.values()
        }

    def parameters(self) -> dict[str, VariableInfo]:
        return {
            p.name: VariableInfo(
                type=p.type,
                description=p.description,
                unit=p.unit,
                value=self._read_variable(p),
                min_value=p.min,
                max_value=p.max,
                start_value=p.start,
                variability=p.variability,
            )
            for p in self.model_description.modelVariables
            if p.causality == FMUCausaltyType.PARAMETER
        }

    def step(self, n: int = 1, **input_values: FMUInputType) -> dict[str, FMUInputType]:
        self._check_instantiated()
        self._set_inputs(**input_values)

        for _ in range(n):
            self._do_step()

        outputs = self._read_outputs()
        return outputs

    def advance(self, until: int, **input_values: FMUInputType) -> dict[str, FMUInputType]:
        self._check_instantiated()

        if until < self._current_time:
            raise ValueError("Cannot advance time to a time in the past.")

        self._set_inputs(**input_values)

        while self._current_time < until:
            self._do_step()

        outputs = self._read_outputs()
        return outputs

    def _do_step(self):
        self.fmu.doStep(
            currentCommunicationPoint=self._current_time,
            communicationStepSize=self._step_size,
        )
        self._current_time += self._step_size

    def _read_variable(self, variable: ScalarVariable) -> FMUInputType:
        variable_type = variable.type
        variable_reference = variable.valueReference

        if variable_type == "Real":
            return self.fmu.getReal([variable_reference])[0]
        elif variable_type == "Integer":
            return self.fmu.getInteger([variable_reference])[0]
        elif variable_type == "Boolean":
            return self.fmu.getBoolean([variable_reference])[0]
        elif variable_type == "String":
            return self.fmu.getString([variable_reference])[0]
        raise ValueError(
            f"Unknown variable type '{variable_type}' for variable '{variable.name}'."
        )

    def _write_variable(self, variable: ScalarVariable, value: FMUInputType) -> None:
        variable_type = variable.type
        variable_reference = variable.valueReference

        if variable_type == "Real":
            self.fmu.setReal([variable_reference], [float(value)])
        elif variable_type == "Integer":
            self.fmu.setInteger([variable_reference], [int(value)])
        elif variable_type == "Boolean":
            self.fmu.setBoolean([variable_reference], [bool(value)])
        elif variable_type == "String":
            self.fmu.setString([variable_reference], [str(value)])
        else:
            raise ValueError(
                f"Unknown variable type '{variable_type}' for variable '{variable.name}'."
            )

    def _set_inputs(self, **input_values: FMUInputType) -> None:
        for input_name, input_value in input_values.items():
            _input = self._inputs[input_name]
            self._write_variable(_input, input_value)

    def _read_outputs(self) -> dict[str, FMUInputType]:
        outputs = {
            "current_time": self._current_time,
        }
        if self._output_refs["Real"]:
            real_outputs = self.fmu.getReal(self._output_refs["Real"])
            outputs.update(
                {
                    output_name: output_val
                    for output_name, output_val in zip(
                        self._output_names["Real"], real_outputs, strict=True
                    )
                }
            )

        if self._output_refs["Integer"]:
            integer_outputs = self.fmu.getInteger(self._output_refs["Integer"])
            outputs.update(
                {
                    output_name: output_val
                    for output_name, output_val in zip(
                        self._output_names["Integer"], integer_outputs, strict=True
                    )
                }
            )

        if self._output_refs["Boolean"]:
            boolean_outputs = self.fmu.getBoolean(self._output_refs["Boolean"])
            outputs.update(
                {
                    output_name: bool(output_val)
                    for output_name, output_val in zip(
                        self._output_names["Boolean"], boolean_outputs, strict=True
                    )
                }
            )

        if self._output_refs["String"]:
            string_outputs = self.fmu.getString(self._output_refs["String"])
            outputs.update(
                {
                    output_name: str(output_val)
                    for output_name, output_val in zip(
                        self._output_names["String"], string_outputs, strict=True
                    )
                }
            )

        return outputs

    def change_parameters(self, **parameters: FMUInputType) -> None:
        self._initialize_fmu(init_values=parameters, current_time=self._current_time)
        # Set all inputs to their current values
        for input_value in self._inputs.values():
            value = self._read_variable(input_value)
            self._write_variable(input_value, value)
