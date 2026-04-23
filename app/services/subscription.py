from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest


async def is_subscribed(bot: Bot, channel_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(channel_id, user_id)

        return member.status in ("member", "administrator", "creator")

    except TelegramBadRequest as e:
        print(f"[SUBSCRIPTION ERROR] {e}")
        return False
