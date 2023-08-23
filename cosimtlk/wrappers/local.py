import logging
import shutil
from pathlib import Path
from typing import Any, Optional, Union
from uuid import uuid4

import fmpy
from fmpy.fmi2 import FMU2Slave
from fmpy.model_description import ModelDescription, ScalarVariable

from cosimtlk.models import FMUCausaltyType, FMUInputType
from cosimtlk.wrappers.base import Wrapper

logger = logging.getLogger(__name__)


class FMIWrapper(Wrapper):
    def __init__(
        self,
        path: Union[Path, str],
    ):
        """Simulator using an FMU.

        Args:
            path: Path of the FMU file.
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
        self._input_variables: dict[str, ScalarVariable] = {
            variable.name: variable
            for variable in self.model_description.modelVariables
            if variable.causality == FMUCausaltyType.INPUT
        }
        self._output_variables: dict[str, ScalarVariable] = {
            variable.name: variable
            for variable in self.model_description.modelVariables
            if variable.causality == FMUCausaltyType.OUTPUT
        }
        self._model_parameters: dict[str, ScalarVariable] = {
            variable.name: variable
            for variable in self.model_description.modelVariables
            if variable.causality == FMUCausaltyType.PARAMETER
        }

        # Create maps for faster read of outputs
        self._output_names: dict[str, list[str]] = {
            "Real": [],
            "Integer": [],
            "Boolean": [],
            "String": [],
        }
        self._output_refs: dict[str, list[int]] = {
            "Real": [],
            "Integer": [],
            "Boolean": [],
            "String": [],
        }
        for variable in self.model_description.modelVariables:
            if (
                variable.causality == FMUCausaltyType.OUTPUT
                and variable.name in self._output_variables
            ):
                self._output_names[variable.type].append(variable.name)
                self._output_refs[variable.type].append(variable.valueReference)

        self._instantiated = False
        self._initialized = False
        self.fmu: Optional[FMU2Slave] = None
        self._current_time = 0
        self._step_size = 1

    def _instantiate(self) -> None:
        # Check platform compatibility and recompile if necessary
        self._check_platform_compatibility()

        self._unzipdir = fmpy.extract(self.fmu_path)
        self.fmu = FMU2Slave(
            unzipDirectory=self._unzipdir,
            guid=self.model_description.guid,
            instanceName=f"{uuid4()}",
            modelIdentifier=self.model_description.coSimulation.modelIdentifier,
        )

        # Instantiate FMU
        self.fmu.instantiate(visible=False, callbacks=None, loggingOn=False)
        self._instantiated = True

    def __call__(
        self,
        *,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: Union[int, float] = 0,
        step_size: Union[int, float] = 1,
    ):
        self.initialize(start_values=start_values, start_time=start_time, step_size=step_size)
        return self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self.fmu_path!r})"

    def __del__(self):
        self.close()
        self._free_instance()

    def _check_platform_compatibility(self) -> None:
        if not self._current_platform_is_supported():
            logger.warning(f"{fmpy.platform} is not supported by this FMU, recompiling...")
            fmpy.util.compile_platform_binary(self.fmu_path)
            logger.info(f"Recompiled FMU for platform {fmpy.platform}.")

    def _current_platform_is_supported(self) -> bool:
        current_platform = fmpy.platform
        supported_platforms = fmpy.supported_platforms(self.fmu_path)
        return current_platform in supported_platforms

    @property
    def step_size(self) -> int:
        return self._step_size

    @property
    def current_time(self) -> Union[int, float]:
        return self._current_time

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def info(self) -> dict[str, Any]:
        return {
            "model": {
                "name": self.model_description.modelName,
                "description": self.model_description.description,
                "fmi_version": self.model_description.fmiVersion,
                "guid": self.model_description.guid,
                "generation_tool": self.model_description.generationTool,
                "generation_date": self.model_description.generationDateAndTime,
            },
            "inputs": self._inputs(),
            "outputs": self._outputs(),
            "parameters": self._parameters(),
        }

    def initialize(
        self,
        *,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: Union[int, float] = 0,
        step_size: Union[int, float] = 1,
    ) -> None:
        """Initialize the FMU.

        In this state, equations are active to determine all outputs (and optionally other variables
        exposed by the exporting tool). The variables that can be retrieved by fmi2GetXXX calls are
        (1) defined in the xml file under <ModelStructure><InitialUnknowns>, and
        (2) variables with causality = ′′output′′. Variables with initial = ′′exact′′ and
        variability ≠ "constant", as well as variables with causality = ′′input′′ can be set.
        """
        if not self._instantiated:
            self._instantiate()

        self._current_time = start_time
        self._step_size = step_size

        # Initialize FMU
        self.fmu.setupExperiment(startTime=self._current_time)

        start_values = start_values or {}
        self.fmu.enterInitializationMode()
        fmpy.simulation.apply_start_values(
            self.fmu, self.model_description, start_values=start_values or {}
        )
        self.fmu.exitInitializationMode()
        self._initialized = True

    def close(self) -> None:
        if self._initialized:
            self.fmu.terminate()
            self.fmu.reset()
        self._initialized = False

    def _free_instance(self) -> None:
        if self._instantiated:
            self.fmu.freeInstance()
            shutil.rmtree(self._unzipdir, ignore_errors=True)

    def reset(
        self,
        *,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: Union[int, float] = 0,
        step_size: Union[int, float] = 1,
    ) -> None:
        self._check_is_initialized()
        self.close()
        self.initialize(start_values=start_values, start_time=start_time, step_size=step_size)

    def _check_is_initialized(self):
        if not self._initialized:
            raise RuntimeError("FMU is not initialized.")

    def step(
        self, *, input_values: Optional[dict[str, FMUInputType]] = None
    ) -> dict[str, FMUInputType]:
        self._check_is_initialized()
        self._set_inputs(input_values or {})
        self._do_step()
        outputs = self.read_outputs()
        return outputs

    def advance(
        self, until: int, *, input_values: Optional[dict[str, FMUInputType]] = None
    ) -> dict[str, FMUInputType]:
        self._check_is_initialized()
        if until < self._current_time:
            raise ValueError("Cannot advance time to a time in the past.")

        self._set_inputs(input_values or {})

        while self._current_time < until:
            self._do_step()

        outputs = self.read_outputs()
        return outputs

    def _do_step(self):
        self.fmu.doStep(
            currentCommunicationPoint=self._current_time,
            communicationStepSize=self._step_size,
        )
        self._current_time += self._step_size

    def _set_inputs(self, input_values: dict[str, FMUInputType]) -> None:
        for input_name, input_value in input_values.items():
            _input = self._input_variables[input_name]
            self._write_variable(_input, input_value)

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
        elif variable_type == "Enumeration":
            self.fmu.setInteger([variable_reference], [int(value)])
        else:
            raise ValueError(
                f"Unknown variable type '{variable_type}' for variable '{variable.name}'."
            )

    def read_outputs(self) -> dict[str, FMUInputType]:
        assert self.fmu is not None

        outputs = {
            "current_time": self._current_time,
        }
        if self._output_refs["Real"]:
            real_outputs = self.fmu.getReal(self._output_refs["Real"])
            outputs.update(dict(zip(self._output_names["Real"], real_outputs, strict=True)))

        if self._output_refs["Integer"]:
            integer_outputs = self.fmu.getInteger(self._output_refs["Integer"])
            outputs.update(dict(zip(self._output_names["Integer"], integer_outputs, strict=True)))

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
        elif variable_type == "Enumeration":
            return self.fmu.getInteger([variable_reference])[0]
        raise ValueError(
            f"Unknown variable type '{variable_type}' for variable '{variable.name}'."
        )

    def change_parameters(self, parameters: dict[str, FMUInputType]) -> None:
        start_values = {
            variable.name: self._read_variable(variable)
            for variable in self.model_description.modelVariables
        }
        start_values.update(parameters)
        self.reset(
            start_values=start_values, start_time=self._current_time, step_size=self._step_size
        )

    def _inputs(self) -> dict[str, dict[str, Any]]:
        return {
            i.name: {
                "type": i.type,
                "description": i.description,
                "unit": i.unit,
                "min_value": i.min,
                "max_value": i.max,
                "start_value": i.start,
                "variability": i.variability,
            }
            for i in self._input_variables.values()
        }

    def _outputs(self) -> dict[str, dict[str, Any]]:
        return {
            o.name: {
                "type": o.type,
                "description": o.description,
                "unit": o.unit,
                "min_value": o.min,
                "max_value": o.max,
                "start_value": o.start,
                "variability": o.variability,
            }
            for o in self._output_variables.values()
        }

    def _parameters(self) -> dict[str, dict[str, Any]]:
        return {
            p.name: {
                "type": p.type,
                "description": p.description,
                "unit": p.unit,
                "min_value": p.min,
                "max_value": p.max,
                "start_value": p.start,
                "variability": p.variability,
            }
            for p in self._model_parameters.values()
        }
