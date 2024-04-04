from collections.abc import Callable, Generator

from pandas import DataFrame, Series

from cosimtlk.simulation.entities import Entity


class Input(Entity):
    def __init__(self, name: str, priority: int, *, values: Series):
        """An entity that sets the input of the simulator based on the input date.

        Args:
            name: The name of the entity.
            values: The input data as a Series with a DatetimeIndex.
                The index of the values is used as the time at which the input is set
        """
        super().__init__(name, priority)
        self.values = values
        self._index = 0

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [self.set_inputs_process]

    def set_inputs_process(self):
        while True:
            if self.values.empty or self._index >= len(self.values):
                self.log.warning("no data left!")
                break

            current_time = self.ctx.current_datetime
            next_point_at = self.values.index[self._index]

            if next_point_at <= current_time:
                current_value = self.values.iloc[self._index]
                self.log.debug(f"setting {self.values.name}={current_value}")
                self.ctx.state[self.values.name] = current_value
                self._index += 1
            else:
                next_point_in = int((next_point_at - current_time).total_seconds())
                yield self.wait_for(next_point_in)


class MultiInput(Entity):
    def __init__(self, name: str, priority: int, *, values: DataFrame):
        """An entity that sets the input of the simulator based on the input date.

        Args:
            name: The name of the entity.
            priority: The priority of the entity in the simulation.
            values: The input data as a Series with a DatetimeIndex.
                The index of the values is used as the time at which the input is set
        """
        super().__init__(name, priority)
        self.values = values
        self._index = 0

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [self.set_inputs_process]

    def set_inputs_process(self):
        while True:
            if self.values.empty or self._index >= len(self.values):
                self.log.warning("no data left!")
                break

            current_time = self.ctx.current_datetime
            next_point_at = self.values.index[self._index]

            if next_point_at <= current_time:
                current_values = self.values.iloc[self._index]
                self.log.debug(f"setting {current_values.to_dict()}")
                self.ctx.state.set(**current_values)
                self._index += 1
            else:
                next_point_in = int((next_point_at - current_time).total_seconds())
                yield self.wait_for(next_point_in)
