from pydantic import BaseSettings


class Settings(BaseSettings):
    fmu_dir: str = "./fmus"


settings = Settings()

