import logging

from fastapi import APIRouter, Body
from starlette.responses import JSONResponse

from cosimtlk.app.dependencies import db
from cosimtlk.models import FMUInputType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulators/{id}", tags=["Simulations"])


@router.post("/step")
def step(id: str, n: int = 1, input_values: dict[str, FMUInputType] = Body({})):
    try:
        result = db.get_simulator(id).step(n=n, **input_values)
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    return result


@router.post("/advance")
def advance(id: str, until: int, input_values: dict[str, FMUInputType] = Body({})):
    try:
        result = db.get_simulator(id).advance(until, **input_values)
    except ValueError as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    return result


@router.put("/parameters")
def change_parameters(id: str, parameters: dict[str, FMUInputType] = Body({})):
    try:
        result = db.get_simulator(id).change_parameters(**parameters)
    except ValueError as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    return result


@router.post("/reset")
def reset(
    id: str,
    init_values: dict[str, FMUInputType] = Body(None),
    output_names: list[str] | None = Body(None),
    step_size: int = Body(1),
):
    simulator = db.get(id)["simulator"]
    try:
        simulator.reset(step_size=step_size, output_names=output_names, init_values=init_values)
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    return JSONResponse(status_code=200, content={"message": "Success"})
