import asyncio

from aiogram.enums import ContentType
from aiogram.filters import CommandStart, Command
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument

from core.models import db_helper, WelcomeMessage

from core import settings
from bot.logger import logger
from bot.services import UserService

BOT_TOKEN = settings.bot.token

dp = Dispatcher()

confirming_words = ["да", "yes", "конечно", "отправить", "send", "accept", "absolutely"]
user_service = UserService()


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    username = message.from_user.username
    chat_id = str(message.chat.id)

    async for session in db_helper.session_getter():
        try:
            # Get welcome message
            welcome_message = await WelcomeMessage.get_message(session)

            user = await user_service.get_user(chat_id)
            if not user:
                user = await user_service.create_user(chat_id, username)
                logger.info("Created new user: %s, username: %s", user.tg_user, user.username)

            elif user.username != username:
                user.username = username

                session.add(user)
                await session.commit()
                await session.refresh(user)

                logger.info("Updated username for user %s to %s", user.tg_user, user.username)

            if welcome_message and '{username}' in welcome_message:
                formatted_message = welcome_message.format(username=username or "пользователь")
            else:
                formatted_message = welcome_message

            await message.answer(formatted_message)

        except Exception as e:
            logger.error(f"Database error in start_handler: {e}")
            await message.answer("Извините, произошла ошибка. Пожалуйста, попробуйте позже.")
        finally:
            await session.close()


class AdminBroadcastStates(StatesGroup):
    WAITING_FOR_MESSAGE = State()
    WAITING_FOR_CONFIRMATION = State()


@dp.message(Command("broadcast"))
async def start_broadcast(message: types.Message, state: FSMContext):
    try:
        if not await UserService.is_superuser(str(message.from_user.id)):
            await message.answer("У вас нет прав для выполнения этой команды.")
            return

        await state.set_state(AdminBroadcastStates.WAITING_FOR_MESSAGE)
        await state.update_data(messages=[])

        await message.answer(
            "Введите сообщение для массовой рассылки. Вы можете отправить следующие типы контента:\n\n"
            "• Текст\n"
            "• Фото\n"
            "• Видео\n"
            "• Аудио\n"
            "• Документ\n"
            "• Анимация (GIF)\n"
            "• Голосовое сообщение\n"
            "• Видеозапись\n"
            "• Стикер\n"
            "• Местоположение\n"
            "• Место (venue)\n"
            "• Контакт\n"
            "• Опрос\n\n"
            "Вы можете отправить несколько сообщений разных типов. "
            "Когда закончите, отправьте команду /done для подтверждения рассылки."
        )

    except Exception as e:
        logger.error(f"Error in start_broadcast: {e}")
        await message.answer("Извините, произошла ошибка. Пожалуйста, попробуйте позже.")


# @dp.message(Command("done"))
# async def process_done_command(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     messages = data.get('messages', [])
#
#     if not messages:
#         await message.answer(
#             "Вы не добавили ни одного сообщения для рассылки. Пожалуйста, добавьте хотя бы одно сообщение.")
#         return
#
#     await state.set_state(AdminBroadcastStates.WAITING_FOR_CONFIRMATION)
#     await message.answer(
#         f"Вы добавили {len(messages)} сообщение(й) для рассылки. Вы уверены, что хотите начать рассылку? (да/нет)")

@dp.message(Command("done"))
async def process_done_command(message: types.Message, state: FSMContext):
    data = await state.get_data()
    messages = data.get('messages', [])

    if not messages:
        await message.answer(
            "Вы не добавили ни одного сообщения для рассылки. Пожалуйста, добавьте хотя бы одно сообщение.")
        return

    await message.answer("Вот предварительный просмотр вашей рассылки:")

    # Отправляем предварительный просмотр сообщений
    media_group = []
    document_group = []
    text_messages = []
    other_messages = []

    for msg in messages:
        if msg.content_type == ContentType.TEXT:
            text_messages.append(msg.text)
        elif msg.content_type == ContentType.PHOTO:
            media_group.append(InputMediaPhoto(media=msg.photo[-1].file_id, caption=msg.caption))
        elif msg.content_type == ContentType.VIDEO:
            media_group.append(InputMediaVideo(media=msg.video.file_id, caption=msg.caption))
        elif msg.content_type == ContentType.AUDIO:
            media_group.append(InputMediaAudio(media=msg.audio.file_id, caption=msg.caption))
        elif msg.content_type == ContentType.DOCUMENT:
            document_group.append(InputMediaDocument(media=msg.document.file_id, caption=msg.caption))
        else:
            other_messages.append(msg)

    # Отправка группы медиафайлов (фото, видео, аудио)
    if media_group:
        for i in range(0, len(media_group), 10):
            await message.bot.send_media_group(message.chat.id, media=media_group[i:i+10])

    # Отправка группы документов
    if document_group:
        for i in range(0, len(document_group), 10):
            await message.bot.send_media_group(message.chat.id, media=document_group[i:i+10])

    # Отправка текстовых сообщений
    for text in text_messages:
        await message.answer(text)

    # Отправка остальных типов сообщений
    for msg in other_messages:
        if msg.content_type == ContentType.ANIMATION:
            await message.bot.send_animation(message.chat.id, msg.animation.file_id, caption=msg.caption)
        elif msg.content_type == ContentType.VOICE:
            await message.bot.send_voice(message.chat.id, msg.voice.file_id, caption=msg.caption)
        elif msg.content_type == ContentType.VIDEO_NOTE:
            await message.bot.send_video_note(message.chat.id, msg.video_note.file_id)
        elif msg.content_type == ContentType.STICKER:
            await message.bot.send_sticker(message.chat.id, msg.sticker.file_id)
        elif msg.content_type == ContentType.LOCATION:
            await message.bot.send_location(message.chat.id, msg.location.latitude, msg.location.longitude)
        elif msg.content_type == ContentType.VENUE:
            await message.bot.send_venue(message.chat.id, msg.venue.location.latitude,
                                         msg.venue.location.longitude, msg.venue.title, msg.venue.address)
        elif msg.content_type == ContentType.CONTACT:
            await message.bot.send_contact(message.chat.id, phone_number=msg.contact.phone_number,
                                           first_name=msg.contact.first_name, last_name=msg.contact.last_name)
        elif msg.content_type == ContentType.POLL:
            await message.bot.send_poll(message.chat.id, question=msg.poll.question,
                                        options=[option.text for option in msg.poll.options],
                                        is_anonymous=msg.poll.is_anonymous,
                                        type=msg.poll.type,
                                        allows_multiple_answers=msg.poll.allows_multiple_answers,
                                        correct_option_id=msg.poll.correct_option_id,
                                        explanation=msg.poll.explanation,
                                        open_period=msg.poll.open_period,
                                        close_date=msg.poll.close_date)
        else:
            await message.answer(f"Неподдерживаемый тип сообщения: {msg.content_type}")

    await state.set_state(AdminBroadcastStates.WAITING_FOR_CONFIRMATION)
    await message.answer(
        f"Вы добавили {len(messages)} сообщение(й) для рассылки. Вы уверены, что хотите начать рассылку? (да/нет)")


@dp.message(AdminBroadcastStates.WAITING_FOR_MESSAGE)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append(message)
    await state.update_data(messages=messages)
    await message.answer("Сообщение добавлено в рассылку. Отправьте еще сообщения или используйте /done для завершения.")


@dp.message(AdminBroadcastStates.WAITING_FOR_CONFIRMATION)
async def confirm_broadcast(message: types.Message, state: FSMContext):
    if message.text.lower() not in confirming_words:
        await message.answer("Рассылка отменена.")
        await state.clear()
        return

    data = await state.get_data()
    broadcast_messages = data['messages']

    all_users = await user_service.get_all_users()
    failed_users = []

    for user in all_users:
        try:
            media_group = []
            document_group = []
            text_messages = []
            other_messages = []

            for msg in broadcast_messages:
                if msg.content_type == ContentType.TEXT:
                    text_messages.append(msg.text)
                elif msg.content_type == ContentType.PHOTO:
                    media_group.append(InputMediaPhoto(media=msg.photo[-1].file_id, caption=msg.caption))
                elif msg.content_type == ContentType.VIDEO:
                    media_group.append(InputMediaVideo(media=msg.video.file_id, caption=msg.caption))
                elif msg.content_type == ContentType.AUDIO:
                    media_group.append(InputMediaAudio(media=msg.audio.file_id, caption=msg.caption))
                elif msg.content_type == ContentType.DOCUMENT:
                    document_group.append(InputMediaDocument(media=msg.document.file_id, caption=msg.caption))
                else:
                    other_messages.append(msg)

            # Отправка группы медиафайлов (фото, видео, аудио)
            if media_group:
                for i in range(0, len(media_group), 10):
                    await message.bot.send_media_group(int(user.tg_user), media=media_group[i:i+10])

            # Отправка группы документов
            if document_group:
                for i in range(0, len(document_group), 10):
                    await message.bot.send_media_group(int(user.tg_user), media=document_group[i:i+10])

            # Отправка текстовых сообщений
            for text in text_messages:
                await message.bot.send_message(int(user.tg_user), text)

            # Отправка остальных типов сообщений
            for msg in other_messages:
                if msg.content_type == ContentType.ANIMATION:
                    await message.bot.send_animation(int(user.tg_user), msg.animation.file_id, caption=msg.caption)
                elif msg.content_type == ContentType.VOICE:
                    await message.bot.send_voice(int(user.tg_user), msg.voice.file_id, caption=msg.caption)
                elif msg.content_type == ContentType.VIDEO_NOTE:
                    await message.bot.send_video_note(int(user.tg_user), msg.video_note.file_id)
                elif msg.content_type == ContentType.STICKER:
                    await message.bot.send_sticker(int(user.tg_user), msg.sticker.file_id)
                elif msg.content_type == ContentType.LOCATION:
                    await message.bot.send_location(int(user.tg_user), msg.location.latitude, msg.location.longitude)
                elif msg.content_type == ContentType.VENUE:
                    await message.bot.send_venue(int(user.tg_user), msg.venue.location.latitude,
                                                 msg.venue.location.longitude, msg.venue.title, msg.venue.address)
                elif msg.content_type == ContentType.CONTACT:
                    await message.bot.send_contact(int(user.tg_user), phone_number=msg.contact.phone_number,
                                                   first_name=msg.contact.first_name, last_name=msg.contact.last_name)
                elif msg.content_type == ContentType.POLL:
                    await message.bot.send_poll(int(user.tg_user), question=msg.poll.question,
                                                options=[option.text for option in msg.poll.options],
                                                is_anonymous=msg.poll.is_anonymous,
                                                type=msg.poll.type,
                                                allows_multiple_answers=msg.poll.allows_multiple_answers,
                                                correct_option_id=msg.poll.correct_option_id,
                                                explanation=msg.poll.explanation,
                                                open_period=msg.poll.open_period,
                                                close_date=msg.poll.close_date)

        except Exception as e:
            logger.info(f"Failed to send broadcast to user {user.tg_user}: {str(e)}")
            failed_users.append(user.tg_user)
            continue

    if failed_users:
        await message.answer(
            f"Рассылка выполнена, но не удалось отправить сообщение {len(failed_users)} пользователям. "
            f"Пользователи могли не активировать чат с ботом.")
    else:
        await message.answer("Рассылка выполнена успешно всем пользователям.")

    await state.clear()


async def main():
    bot = Bot(token=BOT_TOKEN)

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.exception(f"Error starting bot: {e}")

    finally:

        logger.info("Disposing bot...")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
