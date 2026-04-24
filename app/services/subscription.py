from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest


async def check_subscription(
    bot: Bot,
    user_id: int,
    channel_id: int,
) -> bool:
    """
    Проверяет, подписан ли пользователь на канал
    """

    try:
        member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=user_id,
        )

        return member.status in ("member", "administrator", "creator")

    except TelegramBadRequest:
        # если бот не имеет доступа к каналу или канал неверный
        return False

    except Exception:
        # на всякий случай чтобы не ломать flow
        return False
