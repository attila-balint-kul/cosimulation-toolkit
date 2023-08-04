import logging
from pathlib import Path

from fastapi import FastAPI

from cosimtlk.app.config import settings
from cosimtlk.app.routers import simulators, simulation

logger = logging.getLogger(__name__)

app = FastAPI(title="FMU Simulator")
app.include_router(simulators.router)
app.include_router(simulation.router)


@app.get("/", tags=["FMUs"])
def list_fmus():
    fmu_dir = Path(settings.fmu_dir).resolve()
    return {
        "path": fmu_dir,
        "fmus": [fmu.name for fmu in fmu_dir.glob("*.fmu")],
    }


@app.on_event("shutdown")
def shutdown_event():
    from cosimtlk.app.dependencies import db

    db.close()
