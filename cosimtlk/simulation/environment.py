from datetime import datetime
from typing import Any, Optional, Union
from zoneinfo import ZoneInfo

import simpy as sp
from simpy import Event
from simpy.core import EmptySchedule, SimTime, StopSimulation
from simpy.events import URGENT
from tqdm import tqdm


class Environment(sp.Environment):
    def __init__(self, initial_time: int = 0, tzinfo: ZoneInfo = ZoneInfo("UTC")):
        """Execution environment for an event-based simulation. The passing of time
        is simulated by stepping from event to event.

        This subclass of simpy.Environment and makes the following changes:
        - The simulation time is stored as a unix timestamp and is fixed at second resolution.
          The sub-second resolution is used to set the priority of events which would fire at the same time.
        - The simulation is also aware of the timezone, and the current time can be accessed
          as a timezone aware datetime object.

        Args:
            initial_time: The initial time of the simulation as a unix timestamp.
            tzinfo: The timezone of the simulation.
        """
        super().__init__(initial_time=initial_time)
        self.tzinfo = tzinfo

    @property
    def now(self) -> SimTime:
        """The current simulation time as a float.

        This property is not used in this subclass and is made internal. Use simulation_timestamp instead.
        """
        raise AttributeError(
            "Now is used internally, use simulation_time instead to access the current time."
        )

    @property
    def simulation_timestamp(self) -> int:
        """The current simulation time as a unix timestamp."""
        return int(self._now)

    @property
    def simulation_datetime(self) -> datetime:
        """The current simulation time as a timezone aware datetime object."""
        return datetime.fromtimestamp(int(self._now), tz=self.tzinfo)

    def run(
        self,
        until: Union[SimTime, Event, None] = None,
        progress_bar: bool = True,
    ) -> Optional[Any]:
        """Run the environment until the given event or time.

        Args:
            until: The event or time until which the environment should be run.
            progress_bar: Whether to show a progress bar.

        Returns:
            The value of the event if it was triggered, otherwise None.
        """
        if until is not None:
            if not isinstance(until, Event):
                # Assume that *until* is a number if it is not None and
                # not an event.  Create a Timeout(until) in this case.
                at: SimTime
                if isinstance(until, int):
                    at = until
                else:
                    at = float(until)

                if at <= self._now:
                    raise ValueError(f"until(={at}) must be > the current simulation time.")

                # Schedule the event before all regular timeouts.
                until = Event(self)
                until._ok = True
                until._value = None
                self.schedule(until, URGENT, at - self._now)

            elif until.callbacks is None:
                # Until event has already been processed.
                return until.value

            until.callbacks.append(StopSimulation.callback)

        try:
            if progress_bar:
                pbar = tqdm(total=at - self._now, desc="Simulation progress", unit="s")
                while True:
                    now = self._now
                    self.step()
                    progress = self._now - now
                    pbar.update(progress)
            else:
                while True:
                    self.step()
        except StopSimulation as exc:
            return exc.args[0]  # == until.value
        except EmptySchedule as e:
            if until is not None:
                assert not until.triggered
                raise RuntimeError(
                    f'No scheduled events left but "until" event was not ' f"triggered: {until}"
                ) from e
        return None
