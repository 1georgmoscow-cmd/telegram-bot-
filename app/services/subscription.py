import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

logger = logging.getLogger(__name__)


async def is_subscribed(bot: Bot, channel_id: int | str, user_id: int) -> bool:
    """
    Проверяет подписку пользователя на канал.
    Возвращает True / False
    """

    try:
        member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except TelegramForbiddenError as e:
        # бот не имеет доступа к каналу
        logger.warning(f"Forbidden access to channel: {e}")
        return False

    except TelegramBadRequest as e:
        # неправильный channel_id или user_id
        logger.warning(f"Bad request in subscription check: {e}")
        return False

    except Exception as e:
        # любая другая ошибка — не роняем бота
        logger.exception(f"Unexpected error in subscription check: {e}")
        return False