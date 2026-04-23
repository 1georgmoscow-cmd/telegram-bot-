from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.handlers.ui import show_main_menu

router = Router()


@router.callback_query(F.data == "book")
async def book(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("📅 Запись (будем делать дальше)")


@router.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("📖 Твои записи")


@router.callback_query(F.data == "prices")
async def prices(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("💰 Прайс-лист")


@router.callback_query(F.data == "portfolio")
async def portfolio(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("🖼 Портфолио")


@router.callback_query(F.data == "faq")
async def faq(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("❓ FAQ")


@router.callback_query(F.data == "main_menu")
async def back(callback: CallbackQuery):
    await callback.answer()
    await show_main_menu(callback)