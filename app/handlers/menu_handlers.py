from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.handlers.ui import show_main_menu
from app.keyboards.common import back_to_menu_kb, portfolio_kb

router = Router()


# 🔹 безопасный answer (чтобы не было "loading...")
async def safe_answer(callback: CallbackQuery):
    try:
        await callback.answer()
    except:
        pass


# 📅 Запись
@router.callback_query(F.data == "start_booking")
async def start_booking(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text(
        "📅 Запись\n\nВыбери удобное время (скоро сделаем нормально)",
        reply_markup=back_to_menu_kb()
    )


# 📖 Моя запись
@router.callback_query(F.data == "my_booking")
async def my_booking(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text(
        "📖 Твоя запись\n\n(пока пусто)",
        reply_markup=back_to_menu_kb()
    )


# ❌ Отмена записи
@router.callback_query(F.data == "cancel_my_booking")
async def cancel_booking(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text(
        "❌ Отмена записи\n\nВыбери запись для отмены (скоро добавим)",
        reply_markup=back_to_menu_kb()
    )


# 💰 Прайсы
@router.callback_query(F.data == "prices")
async def prices(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text(
        "💰 Прайсы:\n\n"
        "— Услуга 1: 1000₽\n"
        "— Услуга 2: 2000₽\n"
        "— Услуга 3: 3000₽",
        reply_markup=back_to_menu_kb()
    )


# 🖼 Портфолио
@router.callback_query(F.data == "portfolio")
async def portfolio(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.edit_text(
        "🖼 Портфолио\n\nНажми кнопку ниже 👇",
        reply_markup=portfolio_kb()
    )


# 🔙 Назад в меню
@router.callback_query(F.data == "back_menu")
async def back_menu(callback: CallbackQuery):
    await safe_answer(callback)
    await show_main_menu(callback)


# 🧠 DEBUG (можешь удалить потом)
@router.callback_query()
async def debug_all(callback: CallbackQuery):
    print("CLICK:", callback.data)
    await callback.answer()
