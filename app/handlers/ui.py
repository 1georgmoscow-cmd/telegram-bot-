from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


async def show_main_menu(event: Message | CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
            [InlineKeyboardButton(text="📖 Моя запись", callback_data="my_bookings")],
            [InlineKeyboardButton(text="💰 Прайсы", callback_data="prices")],
            [InlineKeyboardButton(text="🖼 Портфолио", callback_data="portfolio")],
            [InlineKeyboardButton(text="❓ FAQ", callback_data="faq")],
        ]
    )

    text = "🏠 <b>Главное меню</b>"

    # 🔥 если это callback
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb)

    # 🔥 если это message (/start)
    else:
        await event.answer(text, reply_markup=kb)