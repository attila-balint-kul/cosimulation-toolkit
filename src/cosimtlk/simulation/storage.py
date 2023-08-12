from typing import Any


class StateStore:
    namespacer: str = ":"

    def __init__(self) -> None:
        self._state: dict[str, Any] = {}

    def make_namespace(self, *args: str) -> str:
        return self.namespacer.join(args)

    def _slip_namespace(self, item: str) -> list[str]:
        return item.split(self.namespacer)

    def __getitem__(self, item: str) -> Any:
        if self.namespacer in item:
            current_dict = self._state
            keys = self._slip_namespace(item)
            for key in keys[:-1]:
                current_dict = current_dict.get(key, {})
            return current_dict.get(keys[-1])
        return self._state[item]

    def __setitem__(self, key: str, value: Any) -> None:
        if self.namespacer in key:
            current_dict = self._state
            keys = self._slip_namespace(key)
            for key in keys[:-1]:
                current_dict = current_dict.setdefault(key, {})
            current_dict[keys[-1]] = value
        else:
            self._state[key] = value

    def get_all(self, *, namespace: str | None = None) -> dict[str, Any]:
        if namespace is None:
            return self._state
        current_dict = self._state
        keys = self._slip_namespace(namespace)
        for key in keys:
            current_dict = current_dict.get(key, {})
        return current_dict

    def get(self, *key: str, namespace: str | None = None) -> Any | dict[str, Any]:
        if namespace is not None:
            key = [f"{namespace}{self.namespacer}{k}" for k in key]
        if len(key) == 1:
            return self.__getitem__(key[0])
        return {k: self.__getitem__(k) for k in key}

    def set(self, namespace: str | None = None, **states: Any) -> None:
        for key, value in states.items():
            if namespace is not None:
                key = f"{namespace}{self.namespacer}{key}"
            self[key] = value


class Database:
    ...

    def store_observation(self, name: str, value: float | int | bool | str, timestamp: int) -> None:
        ...

    def get_last_setpoint(self, name: str, timestamp: int) -> float | int | bool | str:
        ...
