import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError


async def is_subscribed(bot: Bot, channel_id: str | int, user_id: int) -> bool:
    logging.info(f"[SUB CHECK] user={user_id} channel={channel_id}")

    try:
        return await asyncio.wait_for(
            _check_member(bot, channel_id, user_id),
            timeout=4,  # 💥 защита от зависания
        )

    except asyncio.TimeoutError:
        logging.error("[SUB CHECK] TIMEOUT (Telegram не ответил)")
        return False


async def _check_member(bot: Bot, channel_id: str | int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=user_id
        )

        logging.info(f"[SUB CHECK RESULT] status={member.status}")

        return member.status in ("member", "administrator", "creator")

    except TelegramForbiddenError:
        logging.error("[SUB CHECK] FORBIDDEN (бот без доступа)")
        return False

    except TelegramBadRequest as e:
        logging.error(f"[SUB CHECK] BAD REQUEST: {e}")
        return False

    except Exception as e:
        logging.error(f"[SUB CHECK] UNKNOWN ERROR: {e}")
        return False
