import logging
from typing import Callable, Generator, Union

from pandas import DataFrame, Series

from cosimtlk.simulation.entities import Entity
from cosimtlk.simulation.storage import StateStore

logger = logging.getLogger(__name__)


class Input(Entity):
    def __init__(self, name: str, *, data: Union[Series, DataFrame], state_store: StateStore):
        """An entity that sets the input of the simulator based on the input date.

        Args:
            name: The name of the entity.
            data: The input data. Can be a Series or a DataFrame with a DatetimeIndex.
                The index of the data is used as the time at which the input is set,
                while the name of the columns are used as the name of the inputs.
            state_store: The state store to set the input values in.

        """
        super().__init__(name)
        if isinstance(data, Series):
            data = data.copy().to_frame()
        self.data = data
        self.state_store = state_store
        self._index = 0

    @property
    def processes(self) -> list[Callable[[], Generator]]:
        return [self.set_inputs_process]

    def set_inputs_process(self):
        while True:
            if self.data.empty or self._index >= len(self.data):
                logger.warning(f"{self}: t={self.env.simulation_datetime}, no data left.")
                break

            current_time = self.env.simulation_datetime
            next_point_at = self.data.index[self._index]

            if next_point_at <= current_time:
                next_points = self.data.iloc[self._index].to_dict()
                logger.debug(
                    f"{self}: t={self.env.simulation_datetime}, setting inputs: {next_points}"
                )
                self.state_store.set(**next_points)
                self._index += 1
            else:
                next_point_in = int((next_point_at - current_time).total_seconds())
                yield self.env.timeout(next_point_in)
