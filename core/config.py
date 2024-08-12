import os

from pydantic_settings import BaseSettings
from pydantic import BaseModel, PostgresDsn

from dotenv import load_dotenv
import logging
from pythonjsonlogger import jsonlogger


load_dotenv(".env")

# App ENV variables
APP_RUN_HOST = str(os.getenv("APP_RUN_HOST"))
APP_RUN_PORT = int(os.getenv("APP_RUN_PORT"))
DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1')


# Database ENV variables
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", 10))
POSTGRES_MAX_OVERFLOW = int(os.getenv("POSTGRES_MAX_OVERFLOW", 20))

POSTGRES_ECHO = os.getenv("POSTGRES_ECHO", "False").lower() in ('true', '1')


# SQLAdmin ENV variables
SQLADMIN_SECRET_KEY = os.getenv("SQLADMIN_SECRET_KEY")
SQLADMIN_USERNAME = os.getenv("SQLADMIN_USERNAME")
SQLADMIN_PASSWORD = os.getenv("SQLADMIN_PASSWORD")


# Cache ENV variables
USD_CURRENCY_CACHE_SEC = int(os.getenv("USD_CURRENCY_CACHE_SEC", 1800))
OBJECTS_CACHE_SEC = int(os.getenv("OBJECTS_CACHE_SEC", 60))


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


class SQLAdminConfig(BaseModel):
    secret_key: str = SQLADMIN_SECRET_KEY
    username: str = SQLADMIN_USERNAME
    password: str = SQLADMIN_PASSWORD


class CacheConfig(BaseModel):
    usd_currency_cache_sec: int = USD_CURRENCY_CACHE_SEC
    objects_cache_sec: int = OBJECTS_CACHE_SEC


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    api_prefix: APIPrefixConfig = APIPrefixConfig()
    db: DBConfig = DBConfig()
    admin_panel: SQLAdminConfig = SQLAdminConfig()
    cache: CacheConfig = CacheConfig()


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
    stream_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s:%(lineno)d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(stream_formatter)

    # TODO: write some acceptable naming logic
    new_logger = logging.getLogger("MainLogger")
    new_logger.setLevel(log_level)
    new_logger.addHandler(stream_handler)

    # Hide too many logging information
    # logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    if settings.run.debug:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    return new_logger


logger = setup_logging()


# Debug WARNING
if settings.run.debug:
    logger.warning("DEBUG mode is on!")
    # DB URL
    logger.info("Database URL: %s", settings.db.url)

# Database ECHO WARNING
if settings.db.echo:
    logger.warning("Database ECHO is on!")
