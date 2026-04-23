from aiogram import Router
from aiogram.types import Message

from app.handlers.ui import show_main_menu

router = Router()


@router.message()
async def start_handler(message: Message):
    await show_main_menu(message)