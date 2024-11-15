# handlers/reader.py

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from core.models import db_helper
from core import settings, logger as log
from core.services.text_service import TextService
from core.services.button_service import ButtonService
from .utils import send_or_edit_message


router = Router()


class LargeTextStates(StatesGroup):
    READING = State()


@router.callback_query(LargeTextStates.READING, lambda c: c.data == "current_page_reader")
async def current_page_number(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer(settings.bot_reader_text.reader_page_number_button_ansewer)
    return

def split_text_into_chunks(text: str, max_chunk_size: int) -> list[str]:
    """Split text into chunks respecting HTML markup and size limits."""
    chunks = []
    lines = text.split('\n')
    current_chunk = ""

    for line in lines:
        # Start a new chunk if the line starts with "*** "
        if line.startswith("*** "):
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line[4:] + '\n'
        elif len(current_chunk) + len(line) + 1 <= max_chunk_size:
            current_chunk += line + '\n'
        else:
            # Soft pagination for long lines
            words = line.split()
            for word in words:
                if len(current_chunk) + len(word) + 1 > max_chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                current_chunk += word + ' '
            current_chunk = current_chunk.rstrip() + '\n'

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


@router.message(Command("read"))
@router.callback_query(lambda c: c.data and c.data.startswith("read_"))
async def start_reading(message: types.Message | types.CallbackQuery, state: FSMContext):
    if isinstance(message, types.Message):
        context_marker = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    else:
        context_marker = message.data.split("_", 1)[1] if len(message.data.split("_")) > 1 else None
    
    if not context_marker:
        await send_or_edit_message(message, settings.bot_reader_text.reader_command_error, None)
        return
    
    async for session in db_helper.session_getter():
        try:
            text_service = TextService()
            button_service = ButtonService()
            
            content = await text_service.get_text_with_media(context_marker, session)
            if not content or not content["text"]:
                await send_or_edit_message(
                    message, 
                    settings.bot_reader_text.reader_text_not_found + f"'{context_marker}'", 
                    None
                )
                return
            
            text = content["text"]
            media_url = content["media_urls"][0] if content["media_urls"] else await text_service.get_default_media(session)
            chunk_size = content["chunk_size"] or settings.bot_reader_text.reader_chunks
            
            chunks = split_text_into_chunks(text, chunk_size)
            custom_buttons = await button_service.get_buttons_by_marker(context_marker, session)
            keyboard = create_navigation_keyboard(0, len(chunks), custom_buttons)
            
            await state.update_data(
                chunks=chunks,
                current_chunk=0,
                total_chunks=len(chunks),
                media_url=media_url,
                context_marker=context_marker,
                custom_buttons=custom_buttons
            )
            await state.set_state(LargeTextStates.READING)
            
            await send_chunk(message, chunks[0], keyboard, media_url)
        except Exception as e:
            log.error(f"Error in start_reading: {e}")
        finally:
            await session.close()


@router.callback_query(LargeTextStates.READING)
async def process_reading(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chunks = data.get("chunks", [])
    current_chunk = data.get("current_chunk", 0)
    total_chunks = data.get("total_chunks", 0)
    media_url = data.get("media_url")
    custom_buttons = data.get("custom_buttons", [])
    context_marker = data.get("context_marker")
    
    action = callback_query.data
    
    if action in ["next_page", "prev_page", "current_page"]:
        if action == "next_page" and current_chunk < total_chunks - 1:
            current_chunk += 1
        elif action == "prev_page" and current_chunk > 0:
            current_chunk -= 1


        await state.update_data(current_chunk=current_chunk)
        keyboard = create_navigation_keyboard(current_chunk, total_chunks, custom_buttons)
        await send_chunk(
            callback_query,
            chunks[current_chunk],
            keyboard,
            media_url
        )
    else:
        await process_custom_action(callback_query, action, context_marker, state)


@router.message(LargeTextStates.READING)
async def process_page_input(message: types.Message, state: FSMContext):
    try:
        page_number = int(message.text)
        data = await state.get_data()
        chunks = data.get("chunks", [])
        total_chunks = data.get("total_chunks", 0)
        
        if 1 <= page_number <= total_chunks:
            current_chunk = page_number - 1
            await state.update_data(current_chunk=current_chunk)
            
            media_url = data.get("media_url")
            custom_buttons = data.get("custom_buttons", [])
            
            keyboard = create_navigation_keyboard(current_chunk, total_chunks, custom_buttons)
            await send_chunk(
                message,
                chunks[current_chunk],
                keyboard,
                media_url
            )
        else:
            await message.answer("Page number is out of range.")  # TODO: Move to config
    except ValueError:
        await message.answer("Invalid page number. Should be a number in range of pages count.")  # TODO: Move to config
        pass


async def send_chunk(
    message: types.Message | types.CallbackQuery,
    chunk_text: str,
    keyboard: types.InlineKeyboardMarkup,
    media_url: str
):
    try:
        await send_or_edit_message(
            message,
            text=chunk_text,
            keyboard=keyboard,
            media_url=media_url
        )
    except TelegramBadRequest as e:
        log.error(f"TelegramBadRequest: {e}")
        if "MESSAGE_TOO_LONG" in str(e):
            truncated_text = chunk_text[:4096 - 3] + "..."
            await send_or_edit_message(
                message,
                text=truncated_text,
                keyboard=keyboard,
                media_url=media_url
            )
        else:
            if isinstance(message, types.CallbackQuery):
                await message.message.answer_photo(
                    photo=media_url,
                    caption=chunk_text,
                    reply_markup=keyboard
                )
            else:
                await message.answer_photo(
                    photo=media_url,
                    caption=chunk_text,
                    reply_markup=keyboard
                )


def create_navigation_keyboard(
    current_chunk: int,
    total_chunks: int,
    custom_buttons: list
) -> types.InlineKeyboardMarkup:
    keyboard = []
    
    navigation_row = []
    if current_chunk > 0:
        navigation_row.append(
            types.InlineKeyboardButton(text="◀️", callback_data="prev_page")
        )
    
    navigation_row.append(
        types.InlineKeyboardButton(
            text=f"{current_chunk + 1}/{total_chunks}",
            callback_data="current_page_reader"
        )
    )
    
    if current_chunk < total_chunks - 1:
        navigation_row.append(
            types.InlineKeyboardButton(text="▶️", callback_data="next_page")
        )
    
    if navigation_row:
        keyboard.append(navigation_row)
    
    for button in custom_buttons:
        if button.url:
            keyboard.append([
                types.InlineKeyboardButton(text=button.text, url=button.url)
            ])
        elif button.callback_data:
            keyboard.append([
                types.InlineKeyboardButton(
                    text=button.text,
                    callback_data=button.callback_data
                )
            ])

    keyboard.append([
        types.InlineKeyboardButton(
            text=settings.bot_reader_text.reader_end_reading_to_main,
            callback_data="back_to_start"
        )
    ])
    
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

async def process_custom_action(
    callback_query: types.CallbackQuery,
    action: str,
    context_marker: str,
    state: FSMContext
):  # TODO: Add other actions too
    async for session in db_helper.session_getter():
        try:
            button_service = ButtonService()
            buttons = await button_service.get_buttons_by_marker(context_marker, session)
            button = next((b for b in buttons if b.callback_data == action), None)

            if button:
                if button.url:
                    await callback_query.answer(url=button.url)
                elif action.startswith("show_page_"):
                    await state.clear()
                    from .universal_page import get_content
                    context_marker = action.split("_", 2)[2]
                    text, keyboard, media_url = await get_content(context_marker, session)
                    await send_or_edit_message(
                        callback_query,
                        text,
                        keyboard,
                        media_url
                    )
                elif action.startswith("read_"):
                    await state.clear()
                    await start_reading(callback_query, state)
                else:
                    log.info(f"Executing action for button: {button.text}")
                    await callback_query.answer()
            else:
                log.warning(f"Unknown action: {action} for context: {context_marker}")
                await callback_query.answer(settings.bot_reader_text.reader_action_unkown)
        except Exception as e:
            log.error(f"Error in process_custom_action: {e}")
            await callback_query.answer(
                settings.bot_reader_text.reader_custom_action_processing_error
            )
        finally:
            await session.close()
