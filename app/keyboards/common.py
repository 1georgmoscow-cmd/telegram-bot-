from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# =========================
# 🏠 ГЛАВНОЕ МЕНЮ (CRM FIX)
# =========================
def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 Записаться",
                callback_data="start_booking"
            )
        ],
        [
            InlineKeyboardButton(
                text="📖 Моя запись",
                callback_data="my_booking"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить запись",
                callback_data="cancel_my_booking"
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Прайсы",
                callback_data="prices"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼 Портфолио",
                callback_data="portfolio"
            )
        ],
    ]

    if is_admin:
        buttons.append([
            InlineKeyboardButton(
                text="🛠 Админ-панель",
                callback_data="admin_panel"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================
# 🔙 BACK TO MENU (UNIVERSAL)
# =========================
def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 В меню",
                    callback_data="back_menu"
                )
            ]
        ]
    )


# =========================
# 🖼 PORTFOLIO
# =========================
def portfolio_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Смотреть портфолио",
                    url="https://ru.pinterest.com/crystalwithluv/_created/"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В меню",
                    callback_data="back_menu"
                )
            ],
        ]
    )


# =========================
# 📢 SUBSCRIPTION CHECK
# =========================
def subscription_kb(channel_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Подписаться",
                    url=channel_link
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Проверить подписку",
                    callback_data="check_sub"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В меню",
                    callback_data="back_menu"
                )
            ],
        ]
    )
