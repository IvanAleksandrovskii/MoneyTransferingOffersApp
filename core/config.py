import os
import re

from pydantic_settings import BaseSettings
from pydantic import BaseModel, PostgresDsn

from dotenv import load_dotenv
import logging
from pythonjsonlogger import jsonlogger


load_dotenv(".env")

# App ENV variables
APP_RUN_HOST = str(os.getenv("APP_RUN_HOST", "0.0.0.0"))
APP_RUN_PORT = int(os.getenv("APP_RUN_PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1')


# Database ENV variables
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_ADDRESS = os.getenv("POSTGRES_ADDRESS", "pg")
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
OBJECTS_CACHED_MAX_COUNT = int(os.getenv("OBJECTS_CACHED_MAX_COUNT", 20))

# CORS ENV variables
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")

# TGBot ENV variables
TGBOT_TOKEN = os.getenv("TGBOT_TOKEN")
TGBOT_WELCOME_MESSAGE_CACHED_TIME = int(os.getenv("TGBOT_WELCOME_MESSAGE_CACHED_TIME", 60))
TGBOT_DEBUG = os.getenv("TGBOT_DEBUG", "False").lower() in ('true', '1')
TGBOT_USER_ERROR_MESSAGE = os.getenv("TGBOT_USER_ERROR_MESSAGE", "Извините, произошла ошибка. Пожалуйста, попробуйте позже.")
TGBOT_USER_FALLBACK_GREETING = os.getenv("TGBOT_USER_FALLBACK_GREETING", "Привет, {username}, добро пожаловать!")


class RunConfig(BaseModel):
    host: str = APP_RUN_HOST
    port: int = APP_RUN_PORT
    debug: bool = DEBUG


class APIPrefixConfig(BaseModel):
    prefix: str = "/api"


class DBConfig(BaseModel):
    url: PostgresDsn = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_ADDRESS}:5432/{POSTGRES_DB}"
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
    objects_cached_max_count: int = OBJECTS_CACHED_MAX_COUNT


class MediaConfig(BaseModel):
    root: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media')
    url: str = '/media/'


class CORSAllowedOriginsConfig(BaseModel):
    allowed_origins: list[str] = ALLOWED_ORIGINS


class TGBotConfig(BaseModel):
    token: str = TGBOT_TOKEN
    welcome_message_cached_time: int = TGBOT_WELCOME_MESSAGE_CACHED_TIME
    debug: bool = TGBOT_DEBUG
    user_error_message: str = TGBOT_USER_ERROR_MESSAGE
    fallback_greeting_user_message: str = TGBOT_USER_FALLBACK_GREETING


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    api_prefix: APIPrefixConfig = APIPrefixConfig()
    db: DBConfig = DBConfig()
    admin_panel: SQLAdminConfig = SQLAdminConfig()
    cache: CacheConfig = CacheConfig()
    media: MediaConfig = MediaConfig()
    cors: CORSAllowedOriginsConfig = CORSAllowedOriginsConfig()
    bot: TGBotConfig = TGBotConfig()


settings = Settings()

# Make sure media root exists
os.makedirs(settings.media.root, exist_ok=True)


# Setup logging
def setup_logging() -> logging.Logger:
    """
    Set up logging configuration.

    :return: Configured logger
    """
    log_level = logging.DEBUG if settings.run.debug else logging.ERROR

    # Stream handler for console output
    stream_handler = logging.StreamHandler()
    stream_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s:%(lineno)d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(stream_formatter)

    new_logger = logging.getLogger("APP")
    new_logger.setLevel(log_level)
    new_logger.addHandler(stream_handler)

    # Hide too many logging information
    class NoFaviconFilter(logging.Filter):
        def filter(self, record):
            return not any(x in record.getMessage() for x in ['favicon.ico', 'apple-touch-icon'])

    logging.getLogger("uvicorn").addFilter(NoFaviconFilter())
    logging.getLogger("uvicorn.access").addFilter(NoFaviconFilter())
    logging.getLogger("fastapi").addFilter(NoFaviconFilter())

    logging.getLogger('httpcore').setLevel(logging.ERROR)

    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    if settings.run.debug:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

    return new_logger


logger = setup_logging()


# Debug WARNING
if settings.run.debug:
    logger.warning("DEBUG mode is on!")
    # Regex for login and password searching in URL
    masked_url = re.sub(r'(://[^:]+:)[^@]+(@)', r'\1******\2', settings.db.url)
    # DB URL
    logger.info("Database URL: %s", masked_url)

# Database ECHO WARNING
if settings.db.echo:
    logger.warning("Database ECHO is on!")
