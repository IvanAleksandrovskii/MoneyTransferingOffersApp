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
DEBUG = os.getenv("DEBUG", "True").lower() in ('true', '1')


# Database ENV variables
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres_db_tg_app")
POSTGRES_ADDRESS = os.getenv("POSTGRES_ADDRESS", "0.0.0.0")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

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
TGBOT_URL = os.getenv("TGBOT_URL", "https://f1b0-184-22-9-133.ngrok-free.app")
TGBOT_TOKEN = os.getenv("BOT_TOKEN")
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
    bot: str = os.path.join(root, 'bot')
    url: str = '/media/'


class CORSAllowedOriginsConfig(BaseModel):
    allowed_origins: list[str] = ALLOWED_ORIGINS


class TGBotConfig(BaseModel):
    url: str = TGBOT_URL
    token: str = TGBOT_TOKEN
    welcome_message_cached_time: int = TGBOT_WELCOME_MESSAGE_CACHED_TIME
    debug: bool = TGBOT_DEBUG
    user_error_message: str = TGBOT_USER_ERROR_MESSAGE
    fallback_greeting_user_message: str = TGBOT_USER_FALLBACK_GREETING


class WebhookConfig(BaseModel):
    path: str = "/webhook/bot/"


class BotAdminTexts(BaseModel):
    """
    RUSSIAN VERSION
    """
    full_success_broadcast: str = "Рассылка выполнена успешно: отправлено всем пользователям: "
    not_all_broadcast_1: str = "Рассылка выполнена, успешно отправлено пользователям"
    not_all_broadcast_2: str = "Но не удалось отправить сообщение пользователям:" 
    not_all_broadcast_3: str = "Пользователи могли не активировать чат с ботом."
    unsupported_file_type: str = "Извините, не поддерживаемый тип контента:"
    unsupported_message_type: str = "Неподдерживаемый тип сообщения: "
    broadcast_cancelled: str = "Рассылка отменена"
    added_to_broadcast: str = "Сообщение добавлено в рассылку. Отправьте еще сообщения или используйте /done для завершения."
    boadcast_approve: str = "Вы добавили сообщение(й) для рассылки. Вы уверены, что хотите начать рассылку? (да/нет)"
    braodcast_preview: str = "Вот предварительный просмотр вашей рассылки:"
    empty_broadcast: str = "Вы не добавили ни одного сообщения для рассылки. Пожалуйста, добавьте хотя бы одно сообщение. Вы сможете отменить на разу после этого."
    greeting: str = """Введите сообщение для массовой рассылки. Вы можете отправить следующие типы контента:\n\n
        • Текст\n
        • Фото\n
        • Видео\n
        • Аудио\n
        • Документ\n
        • Анимация (GIF)\n
        • Голосовое сообщение\n
        • Видеозапись\n
        • Стикер\n
        • Местоположение\n
        • Контакт\n
        Вы можете отправить несколько сообщений разных типов. 
        Когда закончите, отправьте команду /done для подтверждения рассылки."""
    no_admin_rules: str = "У вас нет прав для выполнения этой команды."
    error_message: str = "Something went wrong. Please try again later or contact the developer."
    confirming_words: list[str] = ["да", "yes", "конечно", "отправить", "send", "accept", "absolutely", "lf"]


class BotMainPageTexts(BaseModel):
    user_error_message: str = "Что-то пошло не так. Попробуйте позже."
    utils_error_message: str = "Что-то пошло не так. Попробуйте позже."
    welcome_fallback_user_word: str = "пользователь"
    callback_response_back_to_start: str = "Главное меню"


class UniversalPageTexts(BaseModel):
    universal_page_error: str = "An error occurred while loading the page. Please try again."
    universal_page_try_again: str = "An error occurred. Please try starting over."


class BotReaderTexts(BaseModel):
    reader_chunks: int = 500
    reader_command_error: str = "Пожалуйста, укажите идентификатор текста после команды /read"
    reader_text_not_found: str = "Извините, текст не найден: "
    reader_end_reading_to_main: str = "Главное меню"
    reader_custom_action_processing_error: str = "Произошла ошибка при обработке действия. Попробуйте еще раз."
    reader_action_unkown: str = "Неизвестное действие"
    reader_page_load_error: str = "Произошла ошибка при загрузке страницы. Попробуйте еще раз."
    reader_page_number_button_ansewer: str = "Номер страницы, введите в чат"
    page_number_out_of_range: str = "Номер страницы выходит за пределы доступных страниц"
    invalid_page_number: str = "Неверный номер страницы. Должен быть целым числом в диапазоне от 1 до количества страниц"


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    api_prefix: APIPrefixConfig = APIPrefixConfig()
    db: DBConfig = DBConfig()
    admin_panel: SQLAdminConfig = SQLAdminConfig()
    cache: CacheConfig = CacheConfig()
    media: MediaConfig = MediaConfig()
    cors: CORSAllowedOriginsConfig = CORSAllowedOriginsConfig()
    bot: TGBotConfig = TGBotConfig()
    bot_admin_text: BotAdminTexts = BotAdminTexts()
    webhook: WebhookConfig = WebhookConfig()
    bot_main_page_text: BotMainPageTexts = BotMainPageTexts()
    bot_reader_text: BotReaderTexts = BotReaderTexts()
    universal_page_text: UniversalPageTexts = UniversalPageTexts()


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
