from typing import Any, Optional

import requests

from cosimtlk.app.schemas import SimulatorModel
from cosimtlk.models import FMUInputType


class SimulatorClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def __repr__(self):
        return f"SimulatorClient({self.base_url})"

    @classmethod
    def from_parts(cls, host: str = "127.0.0.1", port: int = 8000, *, secure: bool = False):
        return cls(f"http{'s' if secure else ''}://{host}:{port}")

    @staticmethod
    def default_headers(**kwargs) -> dict[str, str]:
        return {
            "accept": "application/json",
            "Content-Type": "application/json",
            **kwargs,
        }

    def _get(self, path: str, **kwargs) -> dict:
        response = self.session.get(self.base_url + path, **kwargs)
        if not response.ok:
            response.raise_for_status()
        return response.json()

    def _post(self, path: str, *, body: dict, **kwargs) -> dict:
        response = self.session.post(
            self.base_url + path,
            headers=self.default_headers(**kwargs.pop("headers", {})),
            json=body,
            **kwargs,
        )
        if not response.ok:
            response.raise_for_status()
        return response.json()

    def _put(self, path: str, *, body: dict, **kwargs) -> dict:
        response = self.session.put(self.base_url + path, json=body, **kwargs)
        if not response.ok:
            response.raise_for_status()
        return response.json()

    def _delete(self, path: str, **kwargs) -> None:
        response = self.session.delete(self.base_url + path, **kwargs)
        if not response.ok:
            response.raise_for_status()
        return None

    def list_fmus(self) -> dict[str, Any]:
        return self._get("/fmus")

    def get_fmu_info(self, fmu: str) -> dict[str, Any]:
        return self._get(f"/fmus/{fmu}/info")

    def list_simulators(self) -> list[SimulatorModel]:
        return [SimulatorModel(**simulator) for simulator in self._get("/simulators")]

    def create_simulator(
        self,
        path: str,
        *,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: int = 0,
        step_size: int = 1,
    ) -> SimulatorModel:
        params = {"fmu": path}
        body = {
            "start_values": start_values or {},
            "start_time": start_time,
            "step_size": step_size,
        }
        response = self._post("/simulators/", params=params, body=body)
        return SimulatorModel(**response)

    def get_simulator(self, id: str):
        response = self._get(f"/simulators/{id}")
        return SimulatorModel(**response)

    def delete_simulator(self, id: str) -> None:
        return self._delete(f"/simulators/{id}")

    def get_outputs(self, id: str) -> dict[str, FMUInputType]:
        return self._get(f"/simulators/{id}/outputs")

    def step(
        self, id: str, *, input_values: Optional[dict[str, FMUInputType]] = None
    ) -> dict[str, FMUInputType]:
        body = input_values or {}
        return self._post(f"/simulators/{id}/step", body=body)

    def advance(
        self,
        id: str,
        until: int,
        *,
        input_values: Optional[dict[str, FMUInputType]] = None,
    ):
        params = {"until": until}
        body = input_values or {}
        return self._post(f"/simulators/{id}/advance", params=params, body=body)

    def change_parameters(
        self,
        id: str,
        *,
        parameters: dict[str, FMUInputType],
    ):
        body = parameters
        return self._put(f"/simulators/{id}/parameters", body=body)

    def reset(
        self,
        id: str,
        *,
        start_values: Optional[dict[str, FMUInputType]] = None,
        start_time: int = 0,
        step_size: int = 1,
    ):
        body = {
            "start_values": start_values or {},
            "start_time": start_time,
            "step_size": step_size,
        }
        return self._post(f"/simulators/{id}/reset", body=body)
