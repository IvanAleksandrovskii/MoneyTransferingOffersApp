from sqlalchemy import Table, Column, String, Integer, DateTime, func, ForeignKey, MetaData, inspect, text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from core import logger

metadata_logg = MetaData()

tg_users = Table(
    'tg_users',
    metadata_logg,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tg_user', String, nullable=False, unique=True, index=True),
    Column('username', String, nullable=True, unique=True, index=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    Column('is_superuser', Boolean, default=False, nullable=False),
)

tg_users_log = Table(
    'tg_users_log',
    metadata_logg,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tg_user', String, ForeignKey('tg_users.tg_user'), nullable=False, index=True),
    Column('url_log', String, nullable=False),
    Column('amount_log', String, nullable=True),
    Column('currency_log', String, nullable=True),
    Column('send_country_log', String, nullable=True),
    Column('receive_country_log', String, nullable=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
)

Base_2 = declarative_base(metadata=metadata_logg)


class TgUser(Base_2):
    __table__ = tg_users
    logs = relationship("TgUserLog", back_populates="user", lazy='noload')

    id = __table__.c.id
    tg_user = __table__.c.tg_user
    username = __table__.c.username
    created_at = __table__.c.created_at
    is_superuser = __table__.c.is_superuser

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
    send_country_log = __table__.c.send_country_log
    receive_country_log = __table__.c.receive_country_log
    created_at = __table__.c.created_at

    def __repr__(self):
        return f"(id={self.id}, url_log={self.url_log}, created_at={self.created_at})"

    def __str__(self):
        return f"(id={self.id}, url_log={self.url_log}, created_at={self.created_at})"


async def add_missing_columns(engine):
    async with engine.begin() as conn:
        inspector = await conn.run_sync(inspect)
        for table in metadata_logg.sorted_tables:
            existing_columns = await conn.run_sync(lambda sync_conn: inspector.get_columns(table.name))
            existing_column_names = {col['name'] for col in existing_columns}
            for column in table.columns:
                if column.name not in existing_column_names:
                    alter_stmt = text(f"ALTER TABLE {table.name} ADD COLUMN {column.name} {column.type}")
                    await conn.execute(alter_stmt)
                    logger.info(f"Added column {column.name} to table {table.name}")


async def check_and_update_tables(engine):
    # First create tables in a separate transaction
    try:
        async with engine.begin() as conn:
            await conn.run_sync(metadata_logg.create_all)
            logger.info("Created all missing tables")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise

    # Wait a moment to ensure database consistency
    import asyncio
    await asyncio.sleep(1)
    
    # Then check for missing columns in a new transaction
    try:
        async with engine.begin() as conn:
            inspector = await conn.run_sync(inspect)
            tables_exist = True
            
            # Verify tables exist
            for table in metadata_logg.sorted_tables:
                if not await conn.run_sync(lambda sync_conn: inspector.has_table(table.name)):
                    tables_exist = False
                    logger.error(f"Table {table.name} was not created successfully")
                    raise Exception(f"Table {table.name} was not created successfully")
            
            if tables_exist:
                await add_missing_columns(engine)
                logger.info("Successfully added any missing columns")
            
    except Exception as e:
        logger.error(f"Error checking/updating columns: {str(e)}")
        raise
