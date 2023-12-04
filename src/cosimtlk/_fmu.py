from __future__ import annotations

import logging
import shutil
from abc import ABCMeta, abstractmethod
from functools import cached_property
from pathlib import Path
from uuid import uuid4

import fmpy
from fmpy.fmi2 import FMU2Slave
from fmpy.model_description import ModelDescription, ScalarVariable

from cosimtlk.client import SimulatorClient
from cosimtlk.models import FMUCausaltyType, FMUInputType

logger = logging.getLogger(__name__)


class FMUInstanceBase(metaclass=ABCMeta):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        raise NotImplementedError

    def check_is_initialized(self, msg: str = "") -> None:
        """Check if the FMU instance is initialized.

        Args:
            msg (optional): Message to raise if not initialized.
        """
        if not self.is_initialized:
            msg = "FMU instance is not initialized. " + msg
            raise RuntimeError(msg)

    @property
    @abstractmethod
    def step_size(self) -> int | float:
        raise NotImplementedError

    @property
    @abstractmethod
    def current_time(self) -> int | float:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def reset(
        self,
        *,
        start_time: int | float,
        step_size: int | float,
        start_values: dict[str, FMUInputType],
    ) -> dict[str, FMUInputType]:
        raise NotImplementedError

    @abstractmethod
    def step(self, *, input_values: dict[str, FMUInputType] | None = None) -> dict[str, FMUInputType]:
        raise NotImplementedError

    @abstractmethod
    def advance(self, until: int, *, input_values: dict[str, FMUInputType] | None = None) -> dict[str, FMUInputType]:
        raise NotImplementedError

    @abstractmethod
    def set_inputs(self, values: dict[str, FMUInputType]) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_outputs(self) -> dict[str, FMUInputType]:
        raise NotImplementedError

    @abstractmethod
    def change_parameters(self, parameters: dict[str, FMUInputType]) -> FMUInstanceBase:
        raise NotImplementedError


class FMUInstance(FMUInstanceBase):
    def __init__(
        self,
        fmu: FMU,
        start_time: int | float,
        step_size: int | float,
        start_values: dict[str, FMUInputType],
    ):
        self._fmu = fmu
        self._current_time = start_time
        self._step_size = step_size

        self._unzipdir = fmpy.extract(self._fmu._fmu_path)
        self._instance = FMU2Slave(
            unzipDirectory=self._unzipdir,
            guid=self._fmu.model_description.guid,
            instanceName=str(uuid4()),
            modelIdentifier=self._fmu.model_description.coSimulation.modelIdentifier,
        )
        # Instantiate FMU
        self._initialized = True
        self._terminated = False

        self._instance.instantiate(visible=False, callbacks=None, loggingOn=False)
        self._initialize(start_values=start_values)

        # Input dict
        self._input_map: dict[str, ScalarVariable] = {input_.name: input_ for input_ in self._fmu.inputs}

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
        for output in self._fmu.outputs:
            self._output_names[output.type].append(output.name)
            self._output_refs[output.type].append(output.valueReference)

    def _initialize(self, start_values: dict[str, FMUInputType]) -> None:
        self._instance.setupExperiment(startTime=self._current_time)
        self._instance.enterInitializationMode()
        fmpy.simulation.apply_start_values(self._instance, self._fmu.model_description, start_values=start_values or {})
        self._instance.exitInitializationMode()
        self._initialized = True
        self._terminated = False

    def __repr__(self):
        return f"{self.__class__.__name__}(model_name={self._fmu.model_description.modelName})"

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def step_size(self) -> int | float:
        """Return the step size of the FMU."""
        return self._step_size

    @property
    def current_time(self) -> int | float:
        """Return the current time of the FMU."""
        return self._current_time

    def _terminate(self):
        if not self._terminated:
            self._instance.terminate()
            self._instance.reset()
            self._terminated = True

    def close(self):
        """Closes the FMU."""
        self._terminate()
        if self.is_initialized:
            try:
                self._instance.freeInstance()
            except Exception as e:
                logger.error("Could not free FMU instance.")
                logger.exception(e)
            shutil.rmtree(self._unzipdir, ignore_errors=True)
        self._initialized = False

    def reset(
        self,
        *,
        start_time: int | float,
        step_size: int | float,
        start_values: dict[str, FMUInputType],
    ) -> FMUInstanceBase:
        """Reset the FMU.

        Args:
            start_time: Start time of the simulation.
            step_size: Step size of the simulation.
            start_values: Start values of the simulation.

        Returns:
            The FMU instance.
        """
        self._terminate()
        self._current_time = start_time
        self._step_size = step_size
        self._initialize(start_values=start_values)
        return self

    def step(self, *, input_values: dict[str, FMUInputType] | None = None) -> dict[str, FMUInputType]:
        """Do a single step of the FMU.

        Args:
            input_values (optional): Input values for the step. Defaults to None.

        Returns:
            The outputs of the FMU.
        """
        self.check_is_initialized(msg="Cannot call step() on an uninitialized fmu.")

        self.set_inputs(input_values or {})
        self._do_step()
        outputs = self.read_outputs()
        return outputs

    def advance(self, until: int, *, input_values: dict[str, FMUInputType] | None = None) -> dict[str, FMUInputType]:
        """Advance the FMU until a given time.

        Args:
            until: Time to advance to.
            input_values (optional): Input values for the advance. Defaults to None.

        Returns:
            The outputs of the FMU.
        """
        self.check_is_initialized(msg="Cannot call advance() on an uninitialized fmu.")

        if until < self._current_time:
            msg = "Cannot advance time to a time in the past."
            raise ValueError(msg)

        self.set_inputs(input_values or {})

        while self._current_time < until:
            self._do_step()

        outputs = self.read_outputs()
        return outputs

    def _do_step(self):
        self._instance.doStep(
            currentCommunicationPoint=self._current_time,
            communicationStepSize=self._step_size,
        )
        self._current_time += self._step_size

    def set_inputs(self, values: dict[str, FMUInputType]) -> None:
        """Sets the inputs of the FMU.

        Args:
            values: Input values to set. Keys are the names of the FMU inputs.
        """
        self.check_is_initialized(msg="Cannot set inputs on an uninitialized FMU.")

        for input_name, input_value in values.items():
            input_ = self._input_map[input_name]
            self._write_variable(input_, input_value)

    def _write_variable(self, variable: ScalarVariable, value: FMUInputType) -> None:
        variable_type = variable.type
        variable_reference = variable.valueReference

        if variable_type == "Real":
            self._instance.setReal([variable_reference], [float(value)])
        elif variable_type == "Integer":
            self._instance.setInteger([variable_reference], [int(value)])
        elif variable_type == "Boolean":
            self._instance.setBoolean([variable_reference], [bool(value)])
        elif variable_type == "String":
            self._instance.setString([variable_reference], [str(value)])
        elif variable_type == "Enumeration":
            self._instance.setInteger([variable_reference], [int(value)])
        else:
            msg = f"Unknown variable type '{variable_type}' for variable '{variable.name}'."
            raise ValueError(msg)

    def _read_variable(self, variable: ScalarVariable) -> FMUInputType:
        variable_type = variable.type
        variable_reference = variable.valueReference

        if variable_type == "Real":
            return self._instance.getReal([variable_reference])[0]
        elif variable_type == "Integer":
            return self._instance.getInteger([variable_reference])[0]
        elif variable_type == "Boolean":
            return self._instance.getBoolean([variable_reference])[0]
        elif variable_type == "String":
            return self._instance.getString([variable_reference])[0]
        elif variable_type == "Enumeration":
            return self._instance.getInteger([variable_reference])[0]
        msg = f"Unknown variable type '{variable_type}' for variable '{variable.name}'."
        raise ValueError(msg)

    def read_outputs(self) -> dict[str, FMUInputType]:
        """Read the outputs of the FMU.

        Returns:
            The outputs of the FMU.
        """
        self.check_is_initialized(msg="Cannot read outputs on an uninitialized FMU.")

        outputs = {"current_time": self._current_time}

        if self._output_refs["Real"]:
            real_outputs = [float(v) for v in self._instance.getReal(self._output_refs["Real"])]
            outputs.update(dict(zip(self._output_names["Real"], real_outputs, strict=True)))

        if self._output_refs["Integer"]:
            integer_outputs = [int(v) for v in self._instance.getInteger(self._output_refs["Integer"])]
            outputs.update(dict(zip(self._output_names["Integer"], integer_outputs, strict=True)))

        if self._output_refs["Boolean"]:
            boolean_outputs = [bool(v) for v in self._instance.getBoolean(self._output_refs["Boolean"])]
            outputs.update(dict(zip(self._output_names["Boolean"], boolean_outputs, strict=True)))

        if self._output_refs["String"]:
            string_outputs = [str(v) for v in self._instance.getString(self._output_refs["String"])]
            outputs.update(dict(zip(self._output_names["String"], string_outputs, strict=True)))
        return outputs

    def change_parameters(self, parameters: dict[str, FMUInputType]) -> FMUInstance:
        """Change the parameters of the FMU.

        Args:
            parameters: Parameters to change. Keys are the names of the FMU parameters.

        Returns:
            The FMU instance.
        """
        start_values = {
            variable.name: self._read_variable(variable) for variable in self._fmu.model_description.modelVariables
        }
        start_values.update(parameters)
        self.reset(start_values=start_values, start_time=self._current_time, step_size=self._step_size)
        return self


class RemoteFMUInstance(FMUInstanceBase):
    def __init__(
        self,
        fmu: RemoteFMU,
        start_time: int | float,
        step_size: int | float,
        start_values: dict[str, FMUInputType] | None = None,
    ):
        self._fmu = fmu
        self._client = fmu._client

        self._current_time = start_time
        self._step_size = step_size

        self._id = self._client.create_simulator(
            path=self._fmu._path,
            start_time=start_time,
            step_size=step_size,
            start_values=start_values,
        ).id
        self._initialized = True

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self._id}, model_name={self._fmu.model_description.modelName})"

    @property
    def id(self) -> str:  # noqa: A003
        """Return the id of the FMU instance."""
        return self._id

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def step_size(self) -> int | float:
        """Return the step size of the FMU."""
        return self._step_size

    @property
    def current_time(self) -> int | float:
        """Return the current time of the FMU."""
        return self._current_time

    def close(self) -> None:
        """Closes the FMU."""
        if self._initialized:
            self._client.delete_simulator(self._id)
            self._id = None
        self._initialized = False

    def reset(
        self,
        *,
        start_time: int | float,
        step_size: int | float,
        start_values: dict[str, FMUInputType],
    ) -> RemoteFMUInstance:
        """Reset the FMU.

        Args:
            start_time: Start time of the simulation.
            step_size: Step size of the simulation.
            start_values: Start values of the simulation.

        Returns:
            The FMU instance.
        """
        self._step_size = step_size
        self._current_time = start_time
        self._client.reset(self._id, start_values=start_values, start_time=start_time, step_size=step_size)
        return self

    def step(self, *, input_values: dict[str, FMUInputType] | None = None) -> dict[str, FMUInputType]:
        """Do a single step of the FMU.

        Args:
            input_values (optional): Input values for the step. Defaults to None.

        Returns:
            The outputs of the FMU.
        """
        outputs = self._client.step(self._id, input_values=input_values)
        self._current_time = outputs["current_time"]
        return outputs

    def advance(self, until: int, *, input_values: dict[str, FMUInputType] | None = None) -> dict[str, FMUInputType]:
        """Advance the FMU until a given time.

        Args:
            until: Time to advance to.
            input_values (optional): Input values for the advance. Defaults to None.

        Returns:
            The outputs of the FMU.
        """
        outputs = self._client.advance(self._id, until=until, input_values=input_values)
        self._current_time = outputs["current_time"]
        return outputs

    def set_inputs(self, values: dict[str, FMUInputType]) -> None:
        """Sets the inputs of the FMU.

        Args:
            values: Input values to set. Keys are the names of the FMU inputs.
        """
        self._client.set_inputs(self._id, input_values=values)

    def read_outputs(self) -> dict[str, FMUInputType]:
        """Read the outputs of the FMU.

        Returns:
            The outputs of the FMU.
        """
        return self._client.get_outputs(self._id)

    def change_parameters(self, parameters: dict[str, FMUInputType]) -> RemoteFMUInstance:
        """Change the parameters of the FMU.

        Args:
            parameters: Parameters to change. Keys are the names of the FMU parameters.

        Returns:
            The FMU instance.
        """
        self._client.change_parameters(self._id, parameters=parameters)
        return self


class FMUBase(metaclass=ABCMeta):
    @cached_property
    @abstractmethod
    def model_description(self) -> ModelDescription:
        raise NotImplementedError

    @abstractmethod
    def instantiate(
        self,
        *,
        start_time: int | float,
        step_size: int | float,
        start_values: dict,
        **kwargs,
    ) -> FMUInstanceBase:
        raise NotImplementedError

    @cached_property
    def inputs(self) -> list[ScalarVariable]:
        """Return the inputs of the FMU.

        Returns:
            List of FMU inputs.
        """
        return [
            variable
            for variable in self.model_description.modelVariables
            if variable.causality == FMUCausaltyType.INPUT
        ]

    @cached_property
    def outputs(self) -> list[ScalarVariable]:
        """Return the outputs of the FMU.

        Returns:
            List of FMU outputs.
        """
        return [
            variable
            for variable in self.model_description.modelVariables
            if variable.causality == FMUCausaltyType.OUTPUT
        ]

    @cached_property
    def parameters(self) -> list[ScalarVariable]:
        """Return the parameters of the FMU.

        Returns:
            List of FMU parameters.
        """
        return [
            variable
            for variable in self.model_description.modelVariables
            if variable.causality == FMUCausaltyType.PARAMETER
        ]


class FMU(FMUBase):
    def __init__(self, path: str | Path):
        fmu_path = Path(path).resolve()
        if not fmu_path.exists():
            msg = f"FMU file not found: {fmu_path}"
            raise FileNotFoundError(msg)
        if not fmu_path.suffix == ".fmu":
            msg = f"FMU file must have .fmu extension: {fmu_path}"
            raise ValueError(msg)

        self._fmu_path = str(fmu_path)

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self._fmu_path})"

    @cached_property
    def model_description(self) -> ModelDescription:
        """Return the model description of the FMU."""
        return fmpy.read_model_description(self._fmu_path)

    def recompile(self) -> None:
        """Recompile the FMU for the current platform."""
        fmpy.util.compile_platform_binary(self._fmu_path)
        logger.info(f"Recompiled FMU for platform {fmpy.platform}.")

    def current_platform_is_supported(self) -> bool:
        """Check if the current platform is supported by the FMU."""
        current_platform = fmpy.platform
        supported_platforms = fmpy.supported_platforms(self._fmu_path)
        return current_platform in supported_platforms

    def instantiate(
        self,
        *,
        start_time: int | float,
        step_size: int | float,
        start_values: dict | None,
        **kwargs,
    ) -> FMUInstanceBase:
        """Instantiate the FMU.

        Args:
            start_time: Start time of the simulation.
            step_size: Step size of the simulation.
            start_values (optional): Start values of the simulation. Defaults to None.
            recompile (optional): Recompile the FMU for the current platform if not supported. Defaults to False.

        Returns:
            FMUInstance: The instantiated FMU.
        """
        recompile = kwargs.get("recompile", False)
        if recompile and not self.current_platform_is_supported():
            logger.warning(f"{fmpy.platform} is not supported by this FMU, recompiling...")
            self.recompile()

        return FMUInstance(self, start_time=start_time, step_size=step_size, start_values=start_values)


class RemoteFMU(FMUBase):
    def __init__(self, path: str, *, client: SimulatorClient):
        self._path = path
        self._client = client

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self._path}, client={self._client.base_url})"

    @cached_property
    def model_description(self) -> ModelDescription:
        """Return the model description of the FMU."""
        model_description_dto = self._client.get_fmu_info(self._path)
        model_description = ModelDescription(**model_description_dto)
        # FIXME: cattrs not working here so it is not a full ModelDescription
        # return cattrs.structure(model_description, ModelDescription)
        model_description.modelVariables = [
            ScalarVariable(**variable) for variable in model_description_dto["modelVariables"]
        ]
        return model_description

    def instantiate(
        self,
        *,
        start_time: int | float,
        step_size: int | float,
        start_values: dict,
        **kwargs,  # noqa
    ) -> FMUInstanceBase:
        """Instantiate the FMU.

        Args:
            start_time: Start time of the simulation.
            step_size: Step size of the simulation.
            start_values: Start values of the simulation.

        Returns:
            Instantiated RemoteFMUInstance.
        """
        return RemoteFMUInstance(
            self,
            start_time=start_time,
            step_size=step_size,
            start_values=start_values,
        )
