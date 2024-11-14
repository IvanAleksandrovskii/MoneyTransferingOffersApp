# bot/handlers/on_start.py

from aiogram import Router, Bot, types
from aiogram.filters import Command



router = Router()


@router.message(Command("start"))
async def start(callback_query: types.CallbackQuery, bot: Bot):
    await bot.send_message(callback_query.from_user.id, "Hello!")
