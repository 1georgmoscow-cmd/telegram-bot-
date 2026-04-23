from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Записаться", callback_data="book"),
                InlineKeyboardButton(text="📖 Моя запись", callback_data="my_bookings"),
            ],
            [
                InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_booking"),
            ],
            [
                InlineKeyboardButton(text="💰 Прайсы", callback_data="prices"),
                InlineKeyboardButton(text="🖼 Портфолио", callback_data="portfolio"),
            ],
            [
                InlineKeyboardButton(text="❓ FAQ", callback_data="faq"),
            ],
        ]
    )
    from aiogram.types import Message, CallbackQuery


async def show_main_menu(event: Message | CallbackQuery):
    text = "🏠 Главное меню"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=main_menu_kb())
    else:
        await event.answer(text, reply_markup=main_menu_kb())