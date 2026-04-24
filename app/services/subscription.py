from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError


async def is_subscribed(bot: Bot, channel_id: int | str, user_id: int) -> bool:
    """
    Проверка подписки пользователя на канал.
    Без базы данных. Только Telegram API.
    """

    try:
        member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=user_id,
        )

        return member.status in ("member", "administrator", "creator")

    except (TelegramBadRequest, TelegramForbiddenError):
        # если бот не админ в канале или юзер недоступен
        return False

    except Exception:
        # любая другая ошибка = считаем НЕ подписан
        return False
