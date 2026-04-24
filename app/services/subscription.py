from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError


async def is_subscribed(bot: Bot, channel_id, user_id: int) -> bool:
    """
    Проверка подписки пользователя в канале
    channel_id может быть int или str (@channel)
    """

    try:
        member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=user_id,
        )

        return member.status in ("member", "administrator", "creator")

    except TelegramBadRequest:
        return False

    except TelegramForbiddenError:
        # бот не админ в канале или нет доступа
        print("BOT HAS NO ACCESS TO CHANNEL")
        return False
