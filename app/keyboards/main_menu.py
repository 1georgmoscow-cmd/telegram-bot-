from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Запись", callback_data="book"),
            ],
            [
                InlineKeyboardButton(text="📖 Мои записи", callback_data="my_bookings"),
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