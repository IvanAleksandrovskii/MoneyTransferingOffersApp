from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import uvicorn

from core import settings
from core import logger
from core.models import db_helper


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("Starting up the FastAPI application...")

    yield

    # Shutdown
    logger.info("Shutting down the FastAPI application...")
    await db_helper.dispose()

# ORJSONResponse to increase performance
main_app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)

# app.include_router(router = api_router, prefix = settings.api_prefix.prefix, tags = ["API Endpoints"])


if __name__ == "__main__":
    uvicorn.run("main:main_app", host=settings.run.host, port=settings.run.port, reload=settings.run.debug)
