from aiogram.types import CallbackQuery
from app.keyboards.main_menu import main_menu_kb


async def show_main_menu(target):
    text = (
        "🏠 <b>Главное меню</b>\n\n"
        "Выбери действие:"
    )

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text,
            reply_markup=main_menu_kb()
        )
    else:
        await target.answer(text)