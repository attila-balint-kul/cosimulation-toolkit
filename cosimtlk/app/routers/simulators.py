import logging
from pathlib import Path

from fastapi import APIRouter, Body, Response
from starlette.responses import JSONResponse

from cosimtlk.app.config import settings
from cosimtlk.app.schemas import SimulatorCreateModel, SimulatorModel
from cosimtlk.app.services.simulator import simulator_service
from cosimtlk.models import FMUInputType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulators", tags=["Simulators"])


@router.get("/", response_model=list[SimulatorModel])
def list_simulators():
    return [SimulatorModel(**simulator) for simulator in simulator_service.list()]


@router.post("/", response_model=SimulatorModel)
def create_simulator(
    fmu: str,
    data: SimulatorCreateModel,
):
    fmu_path = Path(settings.fmu_dir).resolve() / f"{fmu}.fmu"
    if not fmu_path.exists():
        return Response(status_code=404)

    simulator = simulator_service.create(
        path=fmu_path,
        start_values=data.start_values,
        start_time=data.start_time,
        step_size=data.step_size,
    )
    return simulator


@router.get("/{id}", response_model=SimulatorModel)
def get_simulator(id: str):
    try:
        return simulator_service.get(id)
    except KeyError:
        return Response(status_code=404)


@router.delete("/{id}")
def delete_simulator(id: str):
    try:
        simulator_service.delete(id)
        return Response(status_code=204)
    except KeyError:
        return Response(status_code=404)


@router.get("/{id}/outputs")
def read_outputs(id: str):
    try:
        simulator = simulator_service.get_simulator(id)
        outputs = simulator.read_outputs()
    except KeyError:
        return Response(status_code=404)
    return JSONResponse(status_code=200, content=outputs)


@router.post("/{id}/step")
def step(
    id: str,
    input_values: dict[str, FMUInputType] = Body({}),
):
    try:
        simulator = simulator_service.get_simulator(id)
        result = simulator.step(input_values=input_values)
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    return JSONResponse(status_code=200, content=result)


@router.post("/{id}/advance")
def advance(id: str, until: int, input_values: dict[str, FMUInputType] = Body({})):
    try:
        simulator = simulator_service.get_simulator(id)
        result = simulator.advance(until, input_values=input_values)
    except ValueError as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    return JSONResponse(status_code=200, content=result)


@router.put("/{id}/parameters")
def change_parameters(id: str, parameters: dict[str, FMUInputType] = Body({})):
    try:
        simulator = simulator_service.get_simulator(id)
        simulator.change_parameters(parameters)
    except ValueError as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    return JSONResponse(status_code=200, content={"message": "Success"})


@router.post("/{id}/reset")
def reset(
    id: str,
    data: SimulatorCreateModel,
):
    try:
        simulator = simulator_service.get_simulator(id)
        simulator.reset(
            start_values=data.start_values, start_time=data.start_time, step_size=data.step_size
        )
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    return JSONResponse(status_code=200, content={"message": "Success"})
