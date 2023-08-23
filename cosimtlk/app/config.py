from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    fmu_dir: str = "./fmus"

    class Config:
        env_prefix = "COSIMTLK_"  # defaults to no prefix, i.e. ""


settings = Settings()
