from pydantic_settings import BaseSettings


class RunConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True


class Settings(BaseSettings):
    run: RunConfig = RunConfig()


settings = Settings()
