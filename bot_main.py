import asyncio

from aiogram.enums import ContentType
from aiogram.filters import CommandStart, Command
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.models import db_helper, WelcomeMessage

from core import settings
from bot.bot_logger import logger
from bot.user_service import UserService


BOT_TOKEN = settings.bot.token

dp = Dispatcher()

confirming_words = ["да", "yes", "конечно", "отправить", "send", "accept", "absolutely"]
error_message = ("Извините, произошла ошибка. Пожалуйста, попробуйте позже или обратитесь к разработчику с подробной "
                 "информацией: когда и после какого действия произошла ошибка.")
user_error_message = settings.bot.user_error_message

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
                updated = await user_service.update_username(chat_id, username)
                if updated:
                    logger.info("Updated username for user %s to %s", chat_id, username)
                else:
                    logger.warning("Failed to update username for user %s", chat_id)

                logger.info("Updated username for user %s to %s", user.tg_user, user.username)

            if welcome_message and '{username}' in welcome_message:
                formatted_message = welcome_message.format(username=username or "пользователь")
            else:
                formatted_message = welcome_message

            await message.answer(formatted_message)

        except Exception as e:
            logger.error(f"Database error in start_handler: {e}")

            await message.answer(user_error_message)

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
            "Вы можете отправить несколько сообщений разных типов. "
            "Когда закончите, отправьте команду /done для подтверждения рассылки."
        )

    except Exception as e:
        logger.error(f"Error in start_broadcast: {e}")
        await message.answer(error_message)


@dp.message(Command("done"))
async def process_done_command(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        messages = data.get('messages', [])

        if not messages:
            await message.answer("Вы не добавили ни одного сообщения для рассылки. Пожалуйста, добавьте хотя бы одно сообщение.")
            return

        await message.answer("Вот предварительный просмотр вашей рассылки:")

        for msg_data in messages:
            msg = msg_data['message']
            entities = msg_data['entities']

            if msg.content_type == ContentType.TEXT:
                await message.answer(msg.text, entities=entities)
            elif msg.content_type == ContentType.PHOTO:
                await message.answer_photo(msg.photo[-1].file_id, caption=msg.caption, caption_entities=entities)
            elif msg.content_type == ContentType.VIDEO:
                await message.answer_video(msg.video.file_id, caption=msg.caption, caption_entities=entities)
            elif msg.content_type == ContentType.AUDIO:
                await message.answer_audio(msg.audio.file_id, caption=msg.caption, caption_entities=entities)
            elif msg.content_type == ContentType.DOCUMENT:
                await message.answer_document(msg.document.file_id, caption=msg.caption, caption_entities=entities)
            elif msg.content_type == ContentType.ANIMATION:
                await message.answer_animation(msg.animation.file_id, caption=msg.caption, caption_entities=entities)
            elif msg.content_type == ContentType.VOICE:
                await message.answer_voice(msg.voice.file_id, caption=msg.caption, caption_entities=entities)
            elif msg.content_type == ContentType.VIDEO_NOTE:
                await message.answer_video_note(msg.video_note.file_id)
            elif msg.content_type == ContentType.STICKER:
                await message.answer_sticker(msg.sticker.file_id)
            elif msg.content_type == ContentType.LOCATION:
                await message.answer_location(msg.location.latitude, msg.location.longitude)
            elif msg.content_type == ContentType.VENUE:
                await message.answer_venue(msg.venue.location.latitude, msg.venue.location.longitude, msg.venue.title, msg.venue.address)
            elif msg.content_type == ContentType.CONTACT:
                await message.answer_contact(msg.contact.phone_number, msg.contact.first_name, msg.contact.last_name)
            else:
                await message.answer(f"Неподдерживаемый тип сообщения: {msg.content_type}")

        await state.set_state(AdminBroadcastStates.WAITING_FOR_CONFIRMATION)
        await message.answer(
            f"Вы добавили {len(messages)} сообщение(й) для рассылки. Вы уверены, что хотите начать рассылку? (да/нет)")

    except Exception as e:
        logger.error(f"Error in process_done_command: {e}")
        await message.answer(error_message)


@dp.message(AdminBroadcastStates.WAITING_FOR_MESSAGE)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        messages = data.get('messages', [])

        messages.append({
            'message': message,
            'entities': message.entities or message.caption_entities
        })

        await state.update_data(messages=messages)
        await message.answer("Сообщение добавлено в рассылку. Отправьте еще сообщения или используйте /done для завершения.")
    except Exception as e:
        logger.error(f"Error in process_broadcast_message: {e}")
        await message.answer(error_message)


@dp.message(AdminBroadcastStates.WAITING_FOR_CONFIRMATION)
async def confirm_broadcast(message: types.Message, state: FSMContext):
    try:
        if message.text.lower() not in confirming_words:
            await message.answer("Рассылка отменена.")
            await state.clear()
            return

        data = await state.get_data()
        broadcast_messages = data['messages']

        all_users = await user_service.get_all_users()
        failed_users = []
        users_counter = 0

        for user in all_users:
            try:
                for msg_data in broadcast_messages:
                    msg = msg_data['message']
                    entities = msg_data['entities']

                    if msg.content_type == ContentType.TEXT:
                        await message.bot.send_message(int(user.tg_user), msg.text, entities=entities)
                    elif msg.content_type == ContentType.PHOTO:
                        await message.bot.send_photo(int(user.tg_user), msg.photo[-1].file_id, caption=msg.caption, caption_entities=entities)
                    elif msg.content_type == ContentType.VIDEO:
                        await message.bot.send_video(int(user.tg_user), msg.video.file_id, caption=msg.caption, caption_entities=entities)
                    elif msg.content_type == ContentType.AUDIO:
                        await message.bot.send_audio(int(user.tg_user), msg.audio.file_id, caption=msg.caption, caption_entities=entities)
                    elif msg.content_type == ContentType.DOCUMENT:
                        await message.bot.send_document(int(user.tg_user), msg.document.file_id, caption=msg.caption, caption_entities=entities)
                    elif msg.content_type == ContentType.ANIMATION:
                        await message.bot.send_animation(int(user.tg_user), msg.animation.file_id, caption=msg.caption, caption_entities=entities)
                    elif msg.content_type == ContentType.VOICE:
                        await message.bot.send_voice(int(user.tg_user), msg.voice.file_id, caption=msg.caption, caption_entities=entities)
                    elif msg.content_type == ContentType.VIDEO_NOTE:
                        await message.bot.send_video_note(int(user.tg_user), msg.video_note.file_id)
                    elif msg.content_type == ContentType.STICKER:
                        await message.bot.send_sticker(int(user.tg_user), msg.sticker.file_id)
                    elif msg.content_type == ContentType.LOCATION:
                        await message.bot.send_location(int(user.tg_user), msg.location.latitude, msg.location.longitude)
                    elif msg.content_type == ContentType.VENUE:
                        await message.bot.send_venue(int(user.tg_user), msg.venue.location.latitude, msg.venue.location.longitude, msg.venue.title, msg.venue.address)
                    elif msg.content_type == ContentType.CONTACT:
                        await message.bot.send_contact(int(user.tg_user), msg.contact.phone_number, msg.contact.first_name, msg.contact.last_name)
                    else:
                        await message.bot.send_message(int(user.tg_user), f"Извините, не поддерживаемый тип контента: {msg.content_type}.")

                    users_counter += 1

                    # Sleep to avoid API-flooding/spam block from Telegram
                    await asyncio.sleep(0.05)

            except Exception as e:
                logger.info(f"Failed to send broadcast to user {user.tg_user}: {str(e)}")
                failed_users.append(user.tg_user)
                continue

        if failed_users:
            await message.answer(
                f"Рассылка выполнена, успешно отправлено {users_counter} пользователям, "
                f"но не удалось отправить сообщение {len(failed_users)} пользователям. "
                f"Пользователи могли не активировать чат с ботом.")
        else:
            await message.answer(f"Рассылка выполнена успешно: отправлено всем {users_counter} пользователям.")

        await state.clear()
    except Exception as e:
        logger.error(f"Error in confirm_broadcast: {e}")
        await message.answer(error_message)


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
