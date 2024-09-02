from sqlalchemy import Table, Column, String, Integer, DateTime, func, ForeignKey, MetaData
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

metadata_logg = MetaData()

tg_users = Table(
    'tg_users',
    metadata_logg,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tg_user', String, nullable=False, unique=True, index=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
)

tg_users_log = Table(
    'tg_users_log',
    metadata_logg,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tg_user', String, ForeignKey('tg_users.tg_user'), nullable=False, index=True),
    Column('url_log', String, nullable=False),
    Column('amount_log', String, nullable=False),
    Column('currency_log', String, nullable=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
)

Base_2 = declarative_base(metadata=metadata_logg)


class TgUser(Base_2):
    __table__ = tg_users
    logs = relationship("TgUserLog", back_populates="user", lazy='noload')

    def __repr__(self):
        return f"{self.tg_user}"

    def __str__(self):
        return f"{self.tg_user}"


class TgUserLog(Base_2):
    __table__ = tg_users_log
    user = relationship("TgUser", back_populates="logs")

    id = __table__.c.id
    tg_user = __table__.c.tg_user
    url_log = __table__.c.url_log
    amount_log = __table__.c.amount_log
    currency_log = __table__.c.currency_log
    created_at = __table__.c.created_at

    def __repr__(self):
        return f"(id={self.id}, url_log={self.url_log}, created_at={self.created_at})"

    def __str__(self):
        return f"(id={self.id}, url_log={self.url_log}, created_at={self.created_at})"


async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(metadata_logg.create_all)


async def check_tables_exist(engine):
    async with engine.connect() as conn:
        for table in metadata_logg.sorted_tables:
            exists = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.has_table(sync_conn, table.name)
            )
            if not exists:
                return False
    return True
