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

from aiogram import Bot, Dispatcher
from aiogram.types import WebhookInfo, Update
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from core import settings, logger
from core.models import db_helper, check_and_update_tables
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
    ButtonAdmin,
    MediaAdmin,
    TextAdmin,
)
from core.admin import (
    sqladmin_authentication_backend,
    async_sqladmin_db_helper,
)
# from core.models.tg_welcome_message import check_table
from handlers import router as main_router



# @asynccontextmanager
# async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
#     # Startup
#     logger.info("Starting up the FastAPI application...")

#     # TG logging tables creation
#     engine = db_helper.engine

#     try:
#         logger.info("Checking if logging tables exist...")
#         await check_and_update_tables(engine)

#         # Welcome message for TG bot
#         await check_table(engine)
#     except Exception as e:
#         logger.exception(f"Error in lifespan on table hand writen creation/update (no auto migration tables with ): {e}")

#     yield

#     # Shutdown
#     logger.info("Shutting down the FastAPI application...")
#     await db_helper.dispose()
#     await async_sqladmin_db_helper.dispose()  # Admin db engine dispose

class BotWebhookManager:
    def __init__(self):
        self.bot = None
        self.dp = None
        self.webhook_url = None
        self.webhook_handler = None
        
    async def setup(self, token: str, webhook_host: str, webhook_path: str, router):
        """Initialize bot and webhook configuration"""
        session = AiohttpSession(timeout=60)
        self.bot = Bot(token=token, session=session, default=DefaultBotProperties(parse_mode='HTML'))
        self.dp = Dispatcher()
        self.dp.include_router(router)
        
        # URL for webhook
        self.webhook_url = f"{webhook_host}{webhook_path}"
        
    async def start_webhook(self):
        """Set webhook for the bot"""
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.bot.set_webhook(
            url=self.webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        
        webhook_info: WebhookInfo = await self.bot.get_webhook_info()
        if not webhook_info.url:
            raise RuntimeError("Webhook setup failed!")
        
        logging.info(f"Webhook was set to URL: {webhook_info.url}")
        
    async def stop_webhook(self):
        """Remove webhook and cleanup"""
        if self.bot:
            await self.bot.delete_webhook()
            await self.bot.session.close()

    async def handle_webhook_request(self, request: Request):
        """Handle incoming webhook request from FastAPI"""
        try:
            # Get data from request
            data = await request.json()
            
            # Create Update object from received data
            update = Update(**data)
            
            # Process update
            await self.dp.feed_webhook_update(self.bot, update)
            
            return Response(status_code=200)
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}", exc_info=True)
            return Response(status_code=500)

# Global bot manager instance
bot_manager = BotWebhookManager()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up the FastAPI application...")
    
    # TG logging tables creation
    engine = db_helper.engine
    try:
        logger.info("Checking if logging tables exist...")
        await check_and_update_tables(engine)
    except Exception as e:
        logger.exception(f"Error in lifespan on table hand writen creation/update (no auto migration tables with ): {e}")
    
    await bot_manager.setup(
        token=settings.bot.token,
        webhook_host=settings.bot.url,
        webhook_path=settings.webhook.path,
        router=main_router
    )
    await bot_manager.start_webhook()
    
    yield
    
    logger.info("Shutting down the FastAPI application...")
    await bot_manager.stop_webhook()
    await db_helper.dispose()
    await async_sqladmin_db_helper.dispose()
    
    logger.info("Application shutdown complete")

main_app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

@main_app.post("/webhook/bot/")
async def handle_webhook(request: Request):
    """Endpoint for handling webhooks from Telegram"""
    return await bot_manager.handle_webhook_request(request)


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
    allow_origins=settings.cors.allowed_origins,  # TODO: Cause of webhooks should be all origins allowed
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
admin.add_view(ButtonAdmin)
admin.add_view(MediaAdmin)
admin.add_view(TextAdmin)

main_app.include_router(router=api_router, prefix=settings.api_prefix.prefix)

main_app.mount("/media", StaticFiles(directory=settings.media.root), name="media")

main_app.mount("/app/media/", StaticFiles(directory=settings.media.bot), name="bot_media")


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


if __name__ == '__main__':
    uvicorn.run("main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        # reload=settings.run.debug,
        reload=False,
    )
