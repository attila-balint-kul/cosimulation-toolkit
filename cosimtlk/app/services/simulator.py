from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from cosimtlk import FMIWrapper
from cosimtlk.models import FMUInputType

Record = dict[str, Any]


class SimulatorService:
    def __init__(self):
        self._db: dict[str, Record] = {}

    def close(self) -> None:
        keys = list(self._db.keys())
        for key in keys:
            del self._db[key]

    def create(
        self,
        path: Path,
        *,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: int = 0,
        step_size: int = 1,
    ) -> Record:
        if not path.exists():
            raise FileNotFoundError(path)

        wrapper = FMIWrapper(path)
        fmu = wrapper(
            start_values=start_values or {},
            start_time=start_time,
            step_size=step_size,
        )

        _id = str(uuid4())
        self._db[_id] = {
            "id": _id,
            "fmu": path.stem,
            "simulator": fmu,
            "created_at": datetime.now(tz=ZoneInfo("UTC")).isoformat(),
        }
        return self.get(_id)

    def list(self) -> list[Record]:
        return [self.get(_id) for _id, simulator_record in self._db.items()]

    def get(self, id: str) -> Record:
        return self._db[id]

    def get_simulator(self, id: str) -> FMIWrapper:
        return self._db[id]["simulator"]

    def delete(self, id: str) -> None:
        del self._db[id]


simulator_service = SimulatorService()
