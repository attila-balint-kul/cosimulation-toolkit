from functools import lru_cache
from pathlib import Path

from cosimtlk.app.config import settings


@lru_cache
def get_fmu_dir() -> Path:
    return Path(settings.fmu_dir).resolve()
