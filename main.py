from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
import uvicorn

from core import settings
from core import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("Starting up the FastAPI application...")

    yield

    # Shutdown
    logger.info("Shutting down the FastAPI application...")


main_app = FastAPI(lifespan=lifespan)

# app.include_router(router = api_router, prefix = settings.api_prefix.prefix, tags = ["API Endpoints"])


if __name__ == "__main__":
    uvicorn.run("main:main_app", host=settings.run.host, port=settings.run.port, reload=settings.run.debug)
