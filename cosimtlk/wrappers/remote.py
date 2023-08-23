import logging
from typing import Any, Optional, Union

from cosimtlk.app.client import SimulatorClient
from cosimtlk.models import FMUInputType
from cosimtlk.wrappers.base import Wrapper

logger = logging.getLogger(__name__)


class RemoteFMIWrapper(Wrapper):
    def __init__(self, path: str, client: SimulatorClient):
        self._fmu_path = path
        self.client = client
        self._id = None
        self._step_size = 0
        self._current_time = 0

    def initialize(
        self,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: Union[int, float] = 0,
        step_size: Union[int, float] = 1,
    ) -> None:
        simulator = self.client.create_simulator(
            self._fmu_path, start_values=start_values, start_time=start_time, step_size=step_size
        )
        self._id = simulator.id
        self._step_size = step_size
        self._current_time = start_time

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self._fmu_path}>"

    def __del__(self):
        self.close()

    @property
    def step_size(self) -> int:
        return self._step_size

    @property
    def current_time(self) -> int:
        return self._current_time

    @property
    def is_initialized(self) -> bool:
        return self._id is not None

    def info(self) -> dict[str, Any]:
        self._check_is_initialized()
        return self.client.get_fmu_info(self._fmu_path)

    def close(self):
        if self.is_initialized:
            self.client.delete_simulator(self._id)
            self._id = None

    def reset(
        self,
        *,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: Union[int, float] = 0,
        step_size: Union[int, float] = 1,
    ) -> None:
        self._check_is_initialized()
        self.client.reset(
            self._id, start_values=start_values, start_time=start_time, step_size=step_size
        )
        self._step_size = step_size
        self._current_time = start_time

    def _check_is_initialized(self):
        if self._id is None:
            raise RuntimeError("FMU is not initialized.")

    def step(
        self, *, input_values: Optional[dict[str, FMUInputType]] = None
    ) -> dict[str, FMUInputType]:
        self._check_is_initialized()
        result = self.client.step(self._id, input_values=input_values)
        self._current_time = result["current_time"]
        return result

    def advance(
        self, until: int, *, input_values: Optional[dict[str, FMUInputType]] = None
    ) -> dict[str, FMUInputType]:
        self._check_is_initialized()
        result = self.client.advance(self._id, until, input_values=input_values)
        self._current_time = result["current_time"]
        return result

    def read_outputs(self) -> dict[str, FMUInputType]:
        self._check_is_initialized()
        return self.client.get_outputs(self._id)

    def change_parameters(self, parameters: dict[str, FMUInputType]) -> None:
        self._check_is_initialized()
        self.client.change_parameters(self._id, parameters=parameters)
