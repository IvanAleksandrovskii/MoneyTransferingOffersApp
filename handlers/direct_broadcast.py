# handlers/direct_broadcast.py

import asyncio

from aiogram import types, Router, F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from core import settings, logger as log
from core.services.user_service import UserService


router = Router()


class AdminBroadcastStates(StatesGroup):
    WAITING_FOR_MESSAGE = State()
    WAITING_FOR_CHAT_IDS = State()
    WAITING_FOR_CONFIRMATION = State()
    DIRECT_WAITING_FOR_MESSAGE = State()
    DIRECT_WAITING_FOR_IDS = State()


# Функция для создания клавиатуры с кнопкой отмены
def get_cancel_keyboard():
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="cancel_broadcast")]
        ]
    )
    return keyboard


@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Рассылка отменена.")
    await callback.answer()


@router.message(Command("direct_broadcast"))
async def start_direct_broadcast(message: types.Message, state: FSMContext):
    try:
        if not await UserService.is_superuser(str(message.from_user.id)):
            await message.answer(settings.bot_admin_text.no_admin_rules)
            return

        await state.set_state(AdminBroadcastStates.DIRECT_WAITING_FOR_MESSAGE)
        await state.update_data(messages=[])
        await message.answer(
            "Отправьте сообщения для рассылки. После отправки всех сообщений используйте /next",
            reply_markup=get_cancel_keyboard()
        )

    except Exception as e:
        log.error(f"Error in start_direct_broadcast: {e}")
        await message.answer(settings.bot_admin_text.error_message)


@router.message(Command("next"), AdminBroadcastStates.DIRECT_WAITING_FOR_MESSAGE)
async def process_direct_messages_done(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        messages = data.get('messages', [])

        if not messages:
            await message.answer("Вы не отправили ни одного сообщения для рассылки.")
            return

        await state.set_state(AdminBroadcastStates.DIRECT_WAITING_FOR_IDS)
        await message.answer(
            "Теперь отправьте список ID чатов через запятую.\n"
            "Пример: 123456789, 987654321, 456789123",
            reply_markup=get_cancel_keyboard()
        )

    except Exception as e:
        log.error(f"Error in process_direct_messages_done: {e}")
        await message.answer(settings.bot_admin_text.error_message)


@router.message(AdminBroadcastStates.DIRECT_WAITING_FOR_MESSAGE)
async def process_direct_broadcast_message(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        messages = data.get('messages', [])

        messages.append({
            'message': message,
        })

        await state.update_data(messages=messages)
        await message.answer(
            f"Сообщение добавлено в рассылку. Всего сообщений: {len(messages)}",
            reply_markup=get_cancel_keyboard()
        )
    except Exception as e:
        log.error(f"Error in process_direct_broadcast_message: {e}")
        await message.answer(settings.bot_admin_text.error_message)


@router.message(AdminBroadcastStates.DIRECT_WAITING_FOR_IDS)
async def process_direct_chat_ids(message: types.Message, state: FSMContext):
    try:
        # Разбираем список ID
        chat_ids_raw = message.text.replace(" ", "").split(",")
        chat_ids = []
        invalid_ids = []

        # Проверяем каждый ID
        for id_str in chat_ids_raw:
            try:
                chat_id = int(id_str)
                chat_ids.append(chat_id)
            except ValueError:
                invalid_ids.append(id_str)

        if invalid_ids:
            await message.answer(
                f"Обнаружены некорректные ID: {', '.join(invalid_ids)}\n"
                "Пожалуйста, проверьте список и отправьте снова.",
                reply_markup=get_cancel_keyboard()
            )
            return

        if not chat_ids:
            await message.answer(
                "Не удалось найти корректные ID чатов в вашем сообщении.",
                reply_markup=get_cancel_keyboard()
            )
            return

        # Получаем сообщения для рассылки
        data = await state.get_data()
        broadcast_messages = data.get('messages', [])

        # Начинаем рассылку
        failed_chats = []
        success_counter = 0

        status_message = await message.answer(
            f"Начинаем рассылку в {len(chat_ids)} чатов...",
            reply_markup=get_cancel_keyboard()
        )

        for chat_id in chat_ids:
            # Проверяем не была ли отменена рассылка
            current_state = await state.get_state()
            if current_state is None:  # Состояние было очищено через кнопку отмены
                await status_message.edit_text(
                    f"Рассылка отменена.\n"
                    f"✅ Успешно отправлено: {success_counter} чатов\n"
                    f"❌ Не отправлено: {len(chat_ids) - success_counter} чатов"
                )
                return

            try:
                grouped_media = []
                grouped_documents = []

                for msg_data in broadcast_messages:
                    msg = msg_data['message']

                    if msg.content_type in [ContentType.PHOTO, ContentType.VIDEO]:
                        media = types.InputMediaPhoto(media=msg.photo[-1].file_id) if msg.content_type == ContentType.PHOTO else types.InputMediaVideo(media=msg.video.file_id)
                        media.caption = msg.caption
                        grouped_media.append(media)

                        if len(grouped_media) == 10:
                            await message.bot.send_media_group(chat_id, grouped_media)
                            grouped_media = []

                    elif msg.content_type == ContentType.DOCUMENT:
                        grouped_documents.append((msg.document.file_id, msg.caption))

                        if len(grouped_documents) == 10:
                            for doc in grouped_documents:
                                await message.bot.send_document(chat_id, doc[0], caption=doc[1], parse_mode='HTML')
                            grouped_documents = []

                    else:
                        if grouped_media:
                            await message.bot.send_media_group(chat_id, grouped_media)
                            grouped_media = []
                        if grouped_documents:
                            for doc in grouped_documents:
                                await message.bot.send_document(chat_id, doc[0], caption=doc[1], parse_mode='HTML')
                            grouped_documents = []

                        if msg.content_type == ContentType.TEXT:
                            await message.bot.send_message(chat_id, msg.text, parse_mode='HTML')
                        elif msg.content_type == ContentType.AUDIO:
                            await message.bot.send_audio(chat_id, msg.audio.file_id, caption=msg.caption, parse_mode='HTML')
                        elif msg.content_type == ContentType.ANIMATION:
                            await message.bot.send_animation(chat_id, msg.animation.file_id, caption=msg.caption, parse_mode='HTML')
                        elif msg.content_type == ContentType.VOICE:
                            await message.bot.send_voice(chat_id, msg.voice.file_id, caption=msg.caption, parse_mode='HTML')
                        elif msg.content_type == ContentType.VIDEO_NOTE:
                            await message.bot.send_video_note(chat_id, msg.video_note.file_id)
                        elif msg.content_type == ContentType.STICKER:
                            await message.bot.send_sticker(chat_id, msg.sticker.file_id)
                        elif msg.content_type == ContentType.LOCATION:
                            await message.bot.send_location(chat_id, msg.location.latitude, msg.location.longitude)
                        elif msg.content_type == ContentType.VENUE:
                            await message.bot.send_venue(chat_id, msg.venue.location.latitude, msg.venue.location.longitude, msg.venue.title, msg.venue.address)
                        elif msg.content_type == ContentType.CONTACT:
                            await message.bot.send_contact(chat_id, msg.contact.phone_number, msg.contact.first_name, msg.contact.last_name)
                        else:
                            await message.bot.send_message(chat_id, settings.bot_admin_text.unsupported_file_type + f" {msg.content_type}.")

                if grouped_media:
                    await message.bot.send_media_group(chat_id, grouped_media)
                if grouped_documents:
                    for doc in grouped_documents:
                        await message.bot.send_document(chat_id, doc[0], caption=doc[1], parse_mode='HTML')

                success_counter += 1
                
                # Обновляем статус каждые 10 отправленных сообщений
                if success_counter % 10 == 0:
                    await status_message.edit_text(
                        f"Отправка сообщений...\n"
                        f"✅ Отправлено: {success_counter} из {len(chat_ids)}",
                        reply_markup=get_cancel_keyboard()
                    )
                
                await asyncio.sleep(0.05)  # Anti-flood delay

            except Exception as e:
                log.error(f"Failed to send broadcast to chat {chat_id}: {str(e)}")
                failed_chats.append(chat_id)
                continue

        # Отправляем итоговый отчет
        if failed_chats:
            await status_message.edit_text(
                f"Рассылка завершена частично.\n"
                f"✅ Успешно отправлено: {success_counter} чатов\n"
                f"❌ Ошибки отправки: {len(failed_chats)} чатов\n"
                f"ID чатов с ошибками: {', '.join(map(str, failed_chats))}"
            )
        else:
            await status_message.edit_text(
                f"✅ Рассылка успешно завершена!\n"
                f"Отправлено в {success_counter} чатов"
            )

        await state.clear()

    except Exception as e:
        log.error(f"Error in process_direct_chat_ids: {e}")
        await message.answer(settings.bot_admin_text.error_message)
