from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import uvicorn

from sqladmin import Admin

from core import settings
from core import logger
from core.models import db_helper
from api import api_router, api_router2

from core.admin import *


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("Starting up the FastAPI application...")

    yield

    # Shutdown
    logger.info("Shutting down the FastAPI application...")
    await db_helper.dispose()
    sync_sqladmin_db_helper.dispose()  # Admin db engine dispose

# ORJSONResponse to increase performance
main_app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)

# SQLAdmin
admin = Admin(main_app, engine=db_helper.engine, authentication_backend=sqladmin_authentication_backend)

admin.add_view(CountryAdmin)
admin.add_view(CurrencyAdmin)
admin.add_view(TransferProviderAdmin)
admin.add_view(ProviderExchangeRateAdmin)
admin.add_view(TransferRuleAdmin)

main_app.include_router(router=api_router, prefix=settings.api_prefix.prefix)
main_app.include_router(router=api_router2, prefix=settings.api_prefix.extended)
x

if __name__ == "__main__":
    uvicorn.run("main:main_app", host=settings.run.host, port=settings.run.port, reload=settings.run.debug)
