import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import Response

from cosimtlk.app.dependencies import get_fmu_dir
from cosimtlk.wrappers.local import FMIWrapper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fmus", tags=["FMUs"])


@router.get("/", description="List available FMUs")
def list(fmu_dir: Annotated[Path, Depends(get_fmu_dir)]):
    return {
        "path": fmu_dir,
        "fmus": sorted([fmu.stem for fmu in fmu_dir.glob("*.fmu")]),
    }


@router.get("/{fmu}/info", description="Get information about an FMU")
def get_info(fmu: str, fmu_dir: Annotated[Path, Depends(get_fmu_dir)]):
    fmu_path = fmu_dir / f"{fmu}.fmu"
    if not fmu_path.exists():
        return Response(status_code=404)
    return FMIWrapper(fmu_path).info()
