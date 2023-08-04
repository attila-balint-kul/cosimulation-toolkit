from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cosimtlk.simulator import FMUSimulator

Record = dict[str, Any]


class SimulatorDB:
    def __init__(self):
        self._db: dict[str, Record] = {}

    def close(self) -> None:
        for key in self._db:
            del self._db[key]

    def create(
        self,
        path: Path,
        **kwargs,
    ) -> Record:
        if not path.exists():
            raise FileNotFoundError(path)

        _id = str(uuid4())
        self._db[_id] = {
            "id": _id,
            "fmu": path.stem,
            "simulator": FMUSimulator(path, **kwargs),
            "created_at": datetime.now(),
        }
        return self.get(_id)

    def list(self) -> list[Record]:
        return [self.get(_id) for _id, simulator_record in self._db.items()]

    def get(self, id: str) -> Record:
        return self._db[id]

    def get_simulator(self, id: str) -> FMUSimulator:
        return self._db[id]["simulator"]

    def delete(self, id: str) -> None:
        del self._db[id]


db = SimulatorDB()
