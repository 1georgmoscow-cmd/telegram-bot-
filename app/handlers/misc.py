from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.keyboards.common import main_menu_kb

router = Router()


# =========================
# 🏠 ГЛАВНОЕ МЕНЮ
# =========================
@router.callback_query(F.data == "back_menu")
async def back_menu(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>",
        reply_markup=main_menu_kb(),
    )


# =========================
# 📅 календарь заглушка (обязательная защита)
# =========================
@router.callback_query(F.data == "calendar:noop")
async def calendar_noop(callback: CallbackQuery):
    await callback.answer()


# =========================
# 📖 мои записи (если не реализовано CRM)
# =========================
@router.callback_query(F.data.in_(["my_booking", "my_bookings"]))
async def my_booking(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "📌 Здесь будет твоя запись (CRM модуль в разработке)",
        reply_markup=main_menu_kb(),
    )


# =========================
# 💰 прайсы
# =========================
@router.callback_query(F.data == "prices")
async def prices(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "💰 <b>Прайс пока не настроен</b>",
        reply_markup=main_menu_kb(),
    )


# =========================
# 🖼 портфолио
# =========================
@router.callback_query(F.data == "portfolio")
async def portfolio(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "🖼 <b>Портфолио скоро будет доступно</b>",
        reply_markup=main_menu_kb(),
    )


# =========================
# ❓ FAQ
# =========================
@router.callback_query(F.data == "faq")
async def faq(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "❓ <b>FAQ пока пуст</b>",
        reply_markup=main_menu_kb(),
    )


# =========================
# 🛡 fallback (ловит ВСЁ неизвестное)
# =========================
@router.callback_query()
async def fallback(callback: CallbackQuery):
    """
    Ловит любые несуществующие callback_data
    чтобы бот НЕ падал и не писал 'not handled'
    """
    await callback.answer()

    await callback.message.edit_text(
        "⚠️ Действие недоступно или устарело",
        reply_markup=main_menu_kb(),
    )
