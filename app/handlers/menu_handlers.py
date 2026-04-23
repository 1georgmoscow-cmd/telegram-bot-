from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.handlers.ui import show_main_menu

router = Router()


async def safe_answer(callback: CallbackQuery):
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data == "book")
async def book(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("📅 Запись (скоро сделаем)")


@router.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("📖 Твои записи")


@router.callback_query(F.data == "prices")
async def prices(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("💰 Прайсы")


@router.callback_query(F.data == "portfolio")
async def portfolio(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("🖼 Портфолио")


@router.callback_query(F.data == "faq")
async def faq(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text("❓ FAQ")


@router.callback_query(F.data == "main_menu")
async def back(callback: CallbackQuery):
    await safe_answer(callback)
    await show_main_menu(callback)
