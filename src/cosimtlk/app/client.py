import requests

from cosimtlk.models import SimulatorModel, FMUInputType
from cosimtlk.models import FMUInfo, VariableInfo


class Client:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    @classmethod
    def from_parts(cls, host: str = "127.0.0.1", port: int = 8000, secure: bool = False):
        return cls(f"http{'s' if secure else ''}://{host}:{port}")

    def _get(self, path: str, **kwargs) -> dict:
        response = self.session.get(self.base_url + path, **kwargs)
        if not response.ok:
            response.raise_for_status()
        return response.json()

    def _post(self, path: str, body: dict, **kwargs) -> dict:
        response = self.session.post(self.base_url + path, json=body, **kwargs)
        if not response.ok:
            response.raise_for_status()
        return response.json()

    def _put(self, path: str, body: dict, **kwargs) -> dict:
        response = self.session.put(self.base_url + path, json=body, **kwargs)
        if not response.ok:
            response.raise_for_status()
        return response.json()

    def _delete(self, path: str, **kwargs) -> None:
        response = self.session.delete(self.base_url + path, **kwargs)
        if not response.ok:
            response.raise_for_status()
        return None


class SimulatorClient(Client):
    def list_simulators(self) -> list[SimulatorModel]:
        return [SimulatorModel(**simulator) for simulator in self._get("/simulators")]

    def create_simulator(
        self,
        path: str,
        init_values: dict[str, FMUInputType] | None = None,
        output_names: list[str] | None = None,
        step_size: int = 1,
    ) -> SimulatorModel:
        response = self._post(
            "/simulators",
            params=dict(path=path),
            body={
                "init_values": init_values,
                "output_names": output_names,
                "step_size": step_size,
            },
        )
        return SimulatorModel(**response)

    def get_simulator(self, id: str):
        response = self._get(f"/simulators/{id}")
        return SimulatorModel(**response)

    def delete_simulator(self, id: str) -> None:
        return self._delete(f"/simulators/{id}")

    def get_info(self, id: str) -> FMUInfo:
        response = self._get(f"/simulators/{id}/info")
        return FMUInfo(**response)

    def list_inputs(self, id: str) -> dict[str, VariableInfo]:
        response = self._get(f"/simulators/{id}/inputs")
        print(response)
        return {name: VariableInfo(**variable) for name, variable in response.items()}

    def list_outputs(self, id: str) -> dict[str, VariableInfo]:
        response = self._get(f"/simulators/{id}/outputs")
        return {name: VariableInfo(**variable) for name, variable in response.items()}

    def list_parameters(self, id: str) -> dict[str, VariableInfo]:
        response = self._get(f"/simulators/{id}/parameters")
        return {name: VariableInfo(**variable) for name, variable in response.items()}

    def step(
        self, id: str, n: int = 1, input_values: dict[str, FMUInputType] | None = None
    ) -> dict[str, FMUInputType]:
        return self._post(f"/simulators/{id}/step", params=dict(n=n), body=input_values)

    def advance(
        self,
        id: str,
        until: int,
        input_values: dict[str, FMUInputType] | None = None,
    ):
        return self._post(
            f"/simulators/{id}/advance",
            params=dict(until=until),
            body=input_values,
        )

    def change_parameters(
        self,
        id: str,
        parameters: dict[str, FMUInputType],
    ):
        return self._put(
            f"/simulators/{id}/parameters",
            body=parameters,
        )

    def reset(
        self,
        id: str,
        step_size: int = 1,
        output_names: list[str] | None = None,
        init_values: dict[str, FMUInputType] | None = None,
    ):
        return self._put(
            f"/simulators/{id}/reset",
            body={
                "step_size": step_size,
                "output_names": output_names,
                "init_values": init_values,
            },
        )


class RemoteFMUSimulator:
    def __init__(self, client: SimulatorClient, id: str):
        self.client = client
        self.id = id

    def __str__(self):
        return f"RemoteFMUSimulator({self.id})"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @classmethod
    def new(
        cls,
        client: SimulatorClient,
        path: str,
        init_values: dict[str, FMUInputType] | None = None,
        output_names: list[str] | None = None,
        step_size: int = 1,
    ):
        simulator = client.create_simulator(path, init_values, output_names, step_size)
        return cls(client, simulator.id)

    def info(self) -> FMUInfo:
        return self.client.get_info(self.id)

    def inputs(self) -> dict[str, VariableInfo]:
        return self.client.list_inputs(self.id)

    def outputs(self) -> dict[str, VariableInfo]:
        return self.client.list_outputs(self.id)

    def parameters(self) -> dict[str, VariableInfo]:
        return self.client.list_parameters(self.id)

    def step(self, n: int = 1, **input_values: FMUInputType) -> dict[str, FMUInputType]:
        return self.client.step(self.id, n, input_values)

    def advance(self, until: int, **input_values: FMUInputType) -> dict[str, FMUInputType]:
        return self.client.advance(self.id, until, input_values)

    def change_parameters(self, **parameters: FMUInputType) -> None:
        self.client.change_parameters(self.id, parameters)

    def reset(
        self,
        step_size: int = 1,
        output_names: list[str] | None = None,
        init_values: dict[str, FMUInputType] | None = None,
    ) -> None:
        self.client.reset(self.id, step_size, output_names, init_values)

    def close(self) -> None:
        self.client.delete_simulator(self.id)
