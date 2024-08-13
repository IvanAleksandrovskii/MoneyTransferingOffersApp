from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Response, Request
from fastapi.responses import ORJSONResponse, JSONResponse
import uvicorn

from sqladmin import Admin

from core import settings
from core import logger
from core.models import db_helper
from api import api_router

from core.admin.models import (
    CountryAdmin,
    CurrencyAdmin,
    DocumentAdmin,
    TransferProviderAdmin,
    TransferRuleAdmin,
    ProviderExchangeRateAdmin,
)
from core.admin import (
    sqladmin_authentication_backend,
    async_sqladmin_db_helper,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("Starting up the FastAPI application...")

    yield

    # Shutdown
    logger.info("Shutting down the FastAPI application...")
    await db_helper.dispose()
    await async_sqladmin_db_helper.dispose()  # Admin db engine dispose

# ORJSONResponse to increase performance
main_app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    title="Currency Transfer Rules API",
    description="API for querying provider's money-transfer rules",
)

# SQLAdmin
admin = Admin(main_app, engine=async_sqladmin_db_helper.engine, authentication_backend=sqladmin_authentication_backend)

admin.add_view(CurrencyAdmin)
admin.add_view(CountryAdmin)
admin.add_view(DocumentAdmin)
admin.add_view(TransferProviderAdmin)
admin.add_view(ProviderExchangeRateAdmin)
admin.add_view(TransferRuleAdmin)

main_app.include_router(router=api_router, prefix=settings.api_prefix.prefix)


@main_app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@main_app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    if "badly formed hexadecimal UUID string" in str(exc):
        return JSONResponse(
            status_code=404,
            content={"message": "Resource not found"}
        )
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)}
    )


if __name__ == "__main__":
    uvicorn.run("main:main_app", host=settings.run.host, port=settings.run.port, reload=settings.run.debug)
