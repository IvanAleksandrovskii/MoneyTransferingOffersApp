import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from core.models.tg_logg_user import metadata_logg, check_tables_exist, create_tables


async def recreate_logging_tables():
    # Create async engine
    engine = create_async_engine("postgresql+asyncpg://postgres:password@0.0.0.0:5432/postgres_db_tg_app", echo=True)

    try:
        # Check if tables exist
        print("Checking if logging tables exist...")
        tables_exist = await check_tables_exist(engine)

        if tables_exist:
            print("Logging tables exist. Dropping them...")
            async with engine.begin() as conn:
                await conn.run_sync(metadata_logg.drop_all)
            print("Logging tables dropped successfully.")

        print("Creating logging tables...")
        await create_tables(engine)
        print("Logging tables created successfully.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(recreate_logging_tables())
