from typing import Any

import simpy as sp
from simpy import Event
from simpy.core import EmptySchedule, SimTime, StopSimulation
from simpy.events import URGENT
from tqdm import tqdm


class Environment(sp.Environment):
    def run(
        self,
        until: SimTime | Event | None = None,
        show_progress_bar: bool = True,  # noqa
    ) -> Any | None:
        """Run the environment until the given event or time.

        Args:
            until: The event or time until which the environment should be run.
            show_progress_bar: Whether to show a progress bar.

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
                    msg = f"until(={at}) must be > the current simulation time."
                    raise ValueError(msg)

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
            if show_progress_bar:
                total = at - self._now
                pbar = tqdm(total=total, desc="Simulation progress", unit="s")
                while True:
                    now = int(self._now)
                    self.step()
                    progress = int(self._now) - now
                    if progress > 0:
                        pbar.update(progress)
            else:
                while True:
                    self.step()
        except StopSimulation as exc:
            if show_progress_bar:
                pbar.update(total - pbar.n)
                pbar.close()
            return exc.args[0]  # == until.value
        except EmptySchedule as e:
            if until is not None:
                assert not until.triggered  # noqa: S101
                msg = f'No scheduled events left but "until" event was not triggered: {until}'
                raise RuntimeError(msg) from e
        return None
