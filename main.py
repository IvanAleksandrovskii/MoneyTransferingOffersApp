from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
import uvicorn

from core import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    yield
    # Shutdown


main_app = FastAPI(lifespan=lifespan)

# app.include_router(router, prefix, tags)


if __name__ == "__main__":
    uvicorn.run("main:main_app", host=settings.run.host, port=settings.run.port, reload=settings.run.debug)
