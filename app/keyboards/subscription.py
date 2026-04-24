from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
                    callback_data="check_subscription"
                )
            ],
        ]
    )
