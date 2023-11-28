import logging

from fastapi import FastAPI

from cosimtlk.app.routers import fmus, simulators

logger = logging.getLogger(__name__)

app = FastAPI(title="FMU Simulator")
app.include_router(fmus.router)
app.include_router(simulators.router)


@app.on_event("shutdown")
def shutdown_event():
    from cosimtlk.app.services.simulator import simulator_service

    simulator_service.close()
