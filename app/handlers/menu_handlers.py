from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.handlers.ui import show_main_menu
from app.keyboards.common import back_to_menu_kb, portfolio_kb

router = Router()


async def safe_answer(callback: CallbackQuery):
    try:
        await callback.answer()
    except:
        pass


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


# 🧠 DEBUG (ТОЛЬКО С ТЕГОМ — НЕ ЛОВИТ ВСЁ)
@router.callback_query(F.data.startswith("debug_"))
async def debug(callback: CallbackQuery):
    print("DEBUG:", callback.data)
    await callback.answer()
