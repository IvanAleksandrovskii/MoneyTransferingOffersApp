# handlers/universal_page.py

from aiogram import Router, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import settings, logger as log
from core.models import db_helper
from .utils import send_or_edit_message, get_content
from .on_start import get_start_content


router = Router()


class UniversalPageStates(StatesGroup):
    VIEWING_UNIVERSAL_PAGE = State()

@router.callback_query(lambda c: c.data and c.data.startswith("show_page_"))
async def show_universal_page(callback_query: types.CallbackQuery, state: FSMContext):
    
    await callback_query.answer()

    await state.clear()  # Clear the state before showing a new page
    
    context_marker = callback_query.data.split("_", 2)[2]
    
    log.info("Showing universal page for context_marker: %s", context_marker)
    
    async for session in db_helper.session_getter():
        try:
            text, keyboard, media_url = await get_content(context_marker, session)
            
            await state.set_state(UniversalPageStates.VIEWING_UNIVERSAL_PAGE)
            await state.update_data(current_page=context_marker)
            
            await send_or_edit_message(callback_query, text, keyboard, media_url)
        except Exception as e:
            log.error(f"Error in show_universal_page: {e}")
            await callback_query.answer(settings.universal_page_text.universal_page_error)
            await state.clear()
        finally:
            await session.close()

@router.callback_query(UniversalPageStates.VIEWING_UNIVERSAL_PAGE)
async def process_page_action(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    action = callback_query.data
    log.info("Processing page action: %s", action)

    current_state = await state.get_state()
    if current_state != UniversalPageStates.VIEWING_UNIVERSAL_PAGE:
        log.warning("Unexpected state: %s for action: %s", current_state, action)
        await callback_query.answer(settings.universal_page_text.universal_page_try_again)
        await state.clear()
        return
    
    if action.startswith("show_page_"):
        await show_universal_page(callback_query, state)
    elif action == "back_to_start":
        await state.clear()
        chat_id = callback_query.from_user.id
        username = callback_query.from_user.username
        text, keyboard, media_url = await get_start_content(chat_id, username)
        await send_or_edit_message(callback_query, text, keyboard, media_url)
    
    elif action.startswith("read_"):
        from .reader import start_reading
        await state.clear()
        await start_reading(callback_query, state)
