import logging
from pathlib import Path
from typing import Annotated

import attrs
from fastapi import APIRouter, Depends
from starlette.responses import Response

from cosimtlk._fmu import FMU
from cosimtlk.app.dependencies import get_fmu_dir

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fmus", tags=["FMUs"])


@router.get("/", description="List available FMUs")
def list(fmu_dir: Annotated[Path, Depends(get_fmu_dir)]):  # noqa
    return {
        "path": fmu_dir,
        "fmus": sorted([fmu.stem for fmu in fmu_dir.glob("*.fmu")]),
    }


@router.get("/{fmu}/info", description="Get information about an FMU")
def get_info(fmu: str, fmu_dir: Annotated[Path, Depends(get_fmu_dir)]):
    fmu_path = fmu_dir / f"{fmu}.fmu"
    if not fmu_path.exists():
        return Response(status_code=404)

    model_description = FMU(fmu_path).model_description
    return attrs.asdict(model_description)
