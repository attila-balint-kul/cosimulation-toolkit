from typing import Any


class SimulationState:
    def __setitem__(self, key, value):
        if "." in key:
            keys = key.split(".")
            current = self
            for k in keys[:-1]:
                current = getattr(current, k)
            setattr(current, keys[-1], value)
        else:
            setattr(self, key, value)

    def __getitem__(self, key):
        if "." in key:
            keys = key.split(".")
            current = self
            for k in keys:
                current = getattr(current, k)
            return current
        return getattr(self, key)

    def set(self, **states: Any) -> None:  # noqa: A003
        for key, value in states.items():
            self.__setitem__(key, value)
