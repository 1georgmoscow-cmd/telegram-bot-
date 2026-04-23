from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.handlers.ui import show_main_menu

router = Router()


async def safe_answer(callback: CallbackQuery):
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data == "start_booking")
async def start_booking(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("📅 Запись (скоро сделаем)")


@router.callback_query(F.data == "my_booking")
async def my_booking(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("📖 Твоя запись")


@router.callback_query(F.data == "cancel_my_booking")
async def cancel_booking(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("❌ Отмена записи")


@router.callback_query(F.data == "prices")
async def prices(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("💰 Прайсы")


@router.callback_query(F.data == "portfolio")
async def portfolio(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("🖼 Портфолио")


@router.callback_query(F.data == "back_menu")
async def back(callback: CallbackQuery):
    await safe_answer(callback)
    await show_main_menu(callback)