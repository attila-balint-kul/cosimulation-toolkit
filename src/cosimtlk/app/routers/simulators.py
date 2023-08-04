import logging
from pathlib import Path

from attrs import asdict
from fastapi import APIRouter, Response, Body

from cosimtlk.app.config import settings
from cosimtlk.app.dependencies import db
from cosimtlk.app.schemas import SimulatorModel, SimulatorInfoModel, VariableInfoModel
from cosimtlk.models import FMUInputType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulators", tags=["Simulators"])


@router.get("/", response_model=list[SimulatorModel])
def list_simulators():
    return [SimulatorModel(**simulator) for simulator in db.list()]


@router.post("/", response_model=SimulatorModel)
def create_simulator(
    fmu: str,
    init_values: dict[str, FMUInputType] | None = Body(default=None),
    output_names: list[str] | None = Body(default=None),
    step_size: int = Body(default=1),
):
    fmu_path = Path(settings.fmu_dir).resolve() / f"{fmu}.fmu"
    if not fmu_path.exists():
        return Response(status_code=404)

    simulator = db.create(
        path=fmu_path,
        init_values=init_values,
        output_names=output_names,
        step_size=step_size,
    )
    return SimulatorModel(**simulator)


@router.get("/{id}", response_model=SimulatorModel)
def get_simulator(id: str):
    try:
        return SimulatorModel(**db.get(id))
    except KeyError:
        return Response(status_code=404)


@router.delete("/{id}")
def delete_simulator(
    id: str,
):
    try:
        db.delete(id)
        return Response(status_code=204)
    except KeyError:
        return Response(status_code=404)


@router.get("/{id}/info", response_model=SimulatorInfoModel)
def get_info(id: str):
    simulator = db.get(id)["simulator"]
    return asdict(simulator.info())


@router.get("/{id}/inputs", response_model=dict[str, VariableInfoModel])
def list_inputs(id: str):
    simulator = db.get(id)["simulator"]
    return {k: asdict(v) for k, v in simulator.inputs().items()}


@router.get("/{id}/outputs", response_model=dict[str, VariableInfoModel])
def list_outputs(id: str):
    simulator = db.get(id)["simulator"]
    return {k: asdict(v) for k, v in simulator.outputs().items()}


@router.get("/{id}/parameters", response_model=dict[str, VariableInfoModel])
def list_parameters(id: str):
    simulator = db.get(id)["simulator"]
    return {k: asdict(v) for k, v in simulator.parameters().items()}
