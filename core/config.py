import os

from pydantic_settings import BaseSettings
from pydantic import BaseModel, PostgresDsn

from dotenv import load_dotenv
import logging
from pythonjsonlogger import jsonlogger


load_dotenv(".env")

# App ENV variables
APP_RUN_HOST = str(os.getenv("APP_RUN_HOST", "0.0.0.0"))
APP_RUN_PORT = int(os.getenv("APP_RUN_PORT", 8000))
# TODO: change debug to False by default
DEBUG = os.getenv("DEBUG", "True").lower() in ('true', '1')


# Database ENV variables
# TODO: Delete default values (?)
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres_db_tg_app")

POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", 10))
POSTGRES_MAX_OVERFLOW = int(os.getenv("POSTGRES_MAX_OVERFLOW", 20))

# TODO: change echo to False by default
POSTGRES_ECHO = os.getenv("POSTGRES_ECHO", "True").lower() in ('true', '1')


class RunConfig(BaseModel):
    host: str = APP_RUN_HOST
    port: int = APP_RUN_PORT
    debug: bool = DEBUG


class APIPrefixConfig(BaseModel):
    prefix: str = "/api"


class DBConfig(BaseModel):
    url: PostgresDsn = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@pg:5432/{POSTGRES_DB}"
    pool_size: int = POSTGRES_POOL_SIZE
    max_overflow: int = POSTGRES_MAX_OVERFLOW
    echo: bool = POSTGRES_ECHO

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    api_prefix: APIPrefixConfig = APIPrefixConfig()
    db: DBConfig = DBConfig()


settings = Settings()


# Setup logging
def setup_logging() -> logging.Logger:
    """
    Set up logging configuration.

    :return: Configured logger
    """
    log_level = logging.DEBUG if settings.run.debug else logging.INFO

    # Stream handler for console output
    stream_handler = logging.StreamHandler()
    # TODO: change format up to needed one, now it's made for development debugging
    stream_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s:%(lineno)d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(stream_formatter)

    new_logger = logging.getLogger("Main Logger (form Config)")
    new_logger.setLevel(log_level)
    new_logger.addHandler(stream_handler)

    # Hide too many logging information
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    return new_logger


logger = setup_logging()
