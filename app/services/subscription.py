from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError


async def is_subscribed(bot: Bot, channel_id: str | int, user_id: int) -> bool:
    """
    Проверяет, подписан ли пользователь на канал.
    Работает ТОЛЬКО если бот добавлен в канал админом.
    """

    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)

        status = member.status  # 'member', 'administrator', 'creator', 'left', 'kicked'

        return status in ("member", "administrator", "creator")

    except TelegramForbiddenError:
        # бот не имеет доступа к каналу
        return False

    except TelegramBadRequest:
        # неверный channel_id или пользователь не найден
        return False

    except Exception:
        return False
