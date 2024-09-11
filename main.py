from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from fastapi import FastAPI, Response, Request
from fastapi.responses import ORJSONResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

from sqladmin import Admin
from sqlalchemy.exc import IntegrityError

from core import settings
from core import logger
from core.models import db_helper, check_tables_exist, create_tables
from api import api_router

from core.admin.models import (
    CountryAdmin,
    CurrencyAdmin,
    DocumentAdmin,
    TransferProviderAdmin,
    TransferRuleAdmin,
    ProviderExchangeRateAdmin,
    TgUserAdmin,
    TgUserLogAdmin,
)
from core.admin import (
    sqladmin_authentication_backend,
    async_sqladmin_db_helper,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("Starting up the FastAPI application...")

    # TG logging tables creation
    engine = db_helper.engine
    logger.info("Checking if logging tables exist...")
    tables_exist = await check_tables_exist(engine)
    if tables_exist:
        logger.info("Logging tables already exist")
    if not tables_exist:
        logger.info("Creating logging tables...")
        await create_tables(engine)

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

# Fixing CORS
main_app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLAdmin
admin = Admin(main_app, engine=async_sqladmin_db_helper.engine, authentication_backend=sqladmin_authentication_backend)

admin.add_view(CurrencyAdmin)
admin.add_view(CountryAdmin)
admin.add_view(DocumentAdmin)
admin.add_view(TransferProviderAdmin)
admin.add_view(ProviderExchangeRateAdmin)
admin.add_view(TransferRuleAdmin)
admin.add_view(TgUserAdmin)
admin.add_view(TgUserLogAdmin)

main_app.include_router(router=api_router, prefix=settings.api_prefix.prefix)

main_app.mount("/media", StaticFiles(directory=settings.media.root), name="media")


# Favicon.ico errors silenced
@main_app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# Global exception handler
@main_app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        if request.url.path == "/favicon.ico":
            return Response(status_code=204)

        if isinstance(e, ValueError) and "badly formed hexadecimal UUID string" in str(e):
            return Response(status_code=204)

        if isinstance(e, IntegrityError):
            # Check if error message contains constraint name
            if "duplicate key value violates unique constraint" in str(e):
                # Extract constraint name
                constraint_name = str(e).split('"')[1] if '"' in str(e) else "unknown"
                field = constraint_name.split('_')[-1] if '_' in constraint_name else constraint_name
                logger.warning(f"Attempt to violate unique constraint: {field}")
                return JSONResponse(
                    status_code=409,  # HTTP 409 Conflict
                    content={"message": f"A record with this {field} already exists."}
                )

        logger.exception(f"Unhandled exception: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )


class NoFaviconFilter(logging.Filter):
    def filter(self, record):
        return not any(x in record.getMessage() for x in ['favicon.ico', 'apple-touch-icon'])


logging.getLogger("uvicorn.access").addFilter(NoFaviconFilter())

if __name__ == "__main__":
    uvicorn.run("main:main_app",
                host=settings.run.host,
                port=settings.run.port,
                reload=settings.run.debug,
                access_log=False,
                )
