from __future__ import annotations

import functools
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from cron_converter import Cron


def with_tz(dt: datetime, tzinfo: ZoneInfo = ZoneInfo("UTC")) -> datetime:
    """Add timezone information to a datetime object if missing.

    Args:
        dt: Datetime object with or without timezone information.
        tzinfo: Timezone information to add in case the datetime object has no timezone info.
    """
    tzinfo = dt.tzinfo or tzinfo
    return dt.replace(tzinfo=tzinfo)


def every(*, seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0):
    """Decorator to schedule a process to run forever with a given delay."""
    total_delay_seconds = seconds + minutes * 60 + hours * 3600 + days * 86400
    assert total_delay_seconds > 0, "At least one time unit must be specified."

    def decorator_schedule(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            while True:
                func(self, *args, **kwargs)
                yield self.env.timeout(total_delay_seconds)

        return wrapper

    return decorator_schedule


def cron(*, minute="*", hour="*", day="*", month="*", weekday="*"):
    """Decorator to schedule a process to run forever with a given cron expression."""
    cron_str = " ".join([minute.strip(), hour.strip(), day.strip(), month.strip(), weekday.strip()])
    cron_instance = Cron(cron_str)

    def decorator_cron(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # To return the simulation time as first date if exact match
            last_run = self.env.simulation_datetime
            schedule = cron_instance.schedule(last_run - timedelta(seconds=1))
            while True:
                next_run = schedule.next()
                next_in_seconds = int((next_run - last_run).total_seconds())
                yield self.env.timeout(next_in_seconds)
                func(self, *args, **kwargs)
                last_run = next_run

        return wrapper

    return decorator_cron
