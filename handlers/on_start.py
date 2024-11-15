# bot/handlers/on_start.py

from aiogram import Router, Bot, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core import settings, logger as log
from core.models import db_helper
from core.services.button_service import ButtonService
from core.services.text_service import TextService
from core.services.user_service import UserService
from .utils import send_or_edit_message


router = Router()


async def get_start_content(chat_id: str, username: str | None):
    user_service = UserService()
    text_service = TextService()
    button_service = ButtonService()
    async for session in db_helper.session_getter():
        try:
            user = await user_service.get_user(chat_id)
            if not user:
                user = await user_service.create_user(tg_user=chat_id, username=username)
                log.info("Created new user: %s, username: %s", user.chat_id, user.username)
            elif user.username != username:
                updated = await user_service.update_username(tg_user=chat_id, new_username=username)
                if updated:
                    log.info("Updated username for user %s to %s", chat_id, username)
                else:
                    log.warning("Failed to update username for user %s", chat_id)

            context_marker = "main_page"
            content = await text_service.get_text_with_media(context_marker, session)
            
            if not content:
                log.warning("Content not found for marker: %s", context_marker)
                return settings.bot_main_page_text.user_error_message, None, None

            text = content["text"]
            media_url = content["media_urls"][0] if content["media_urls"] else None

            formatted_text = text.replace("{username}", username or settings.bot_main_page_text.welcome_fallback_user_word)
            
            keyboard = await button_service.create_inline_keyboard(context_marker, session)

            log.debug("Media URL: %s", media_url)
            log.debug("Formatted text: %s", formatted_text)

            if not media_url:
                media_url = await text_service.get_default_media(session)

            return formatted_text, keyboard, media_url
        except Exception as e:
            log.error("Error in get_start_content: %s", e)
            return settings.bot_main_page_text.user_error_message, None, None
        finally:
            await session.close()


@router.message(Command("start"))
async def start_command(message: types.Message, bot: Bot, state: FSMContext):
    """Handler for /start command with promocode support"""
    # args = message.text.split()[1:] 
    chat_id = str(message.chat.id)
    username = message.from_user.username
    
    log.info(f"Start command received. Chat ID: {chat_id}, Username: {username}")

    # Get start content will create user if needed
    text, keyboard, media_url = await get_start_content(chat_id, username)
    await send_or_edit_message(message, text, keyboard, media_url)


@router.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback_query: types.CallbackQuery, state: FSMContext):
    
    await callback_query.answer("Back to start")  # TODO: Move to config
    
    await state.clear()
    chat_id = str(callback_query.from_user.id)
    username = callback_query.from_user.username
    text, keyboard, media_url = await get_start_content(chat_id, username)
    await send_or_edit_message(callback_query.message, text, keyboard, media_url)
