from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest


async def is_subscribed(bot: Bot, channel_id: str | int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=user_id,
        )

        return member.status in ("member", "administrator", "creator")

    except TelegramBadRequest:
        return False

    except Exception:
        return False
