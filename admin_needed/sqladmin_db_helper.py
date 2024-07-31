from sqlalchemy import create_engine, Engine

from core import settings


class SyncDataBaseHelper:
    def __init__(self, url: str, echo: bool):
        self.engine: Engine = create_engine(
            url=url,
            echo=echo,

        )

    def dispose(self):
        self.engine.dispose()


sync_db_url = settings.db.url.replace('postgresql+asyncpg://', 'postgresql://')

sync_sqladmin_db_helper = SyncDataBaseHelper(
    url=sync_db_url,
    echo=False,
)
