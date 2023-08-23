from abc import ABCMeta, abstractmethod
from typing import Any, Optional, Union

from cosimtlk.models import FMUInputType


class Wrapper(metaclass=ABCMeta):
    def __enter__(self) -> "Wrapper":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @abstractmethod
    def info(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def initialize(
        self,
        *,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: Union[int, float] = 0,
        step_size: Union[int, float] = 1,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def reset(
        self,
        *,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: Union[int, float] = 0,
        step_size: Union[int, float] = 1,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def step(
        self,
        *,
        input_values: Optional[dict[str, FMUInputType]] = None,
    ) -> dict[str, FMUInputType]:
        raise NotImplementedError

    @abstractmethod
    def advance(
        self,
        until: int,
        *,
        input_values: Optional[dict[str, FMUInputType]] = None,
    ) -> dict[str, FMUInputType]:
        raise NotImplementedError

    @abstractmethod
    def change_parameters(
        self,
        parameters: dict[str, FMUInputType],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_outputs(self) -> dict[str, FMUInputType]:
        raise NotImplementedError
