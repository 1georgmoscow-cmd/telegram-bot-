from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services.subscription import is_subscribed
from app.handlers.ui import show_main_menu

router = Router()


def get_sub_keyboard(channel_link: str):
    kb = InlineKeyboardBuilder()

    kb.button(text="📢 Подписаться", url=channel_link)
    kb.button(text="✅ Проверить", callback_data="check_sub")

    kb.adjust(1)
    return kb.as_markup()


@router.message(CommandStart())
async def start_handler(message: Message, settings):
    user_id = message.from_user.id

    if not await is_subscribed(
        bot=message.bot,
        channel_id=settings.channel_id,
        user_id=user_id,
    ):
        await message.answer(
            "❌ Подпишись на канал, чтобы пользоваться ботом",
            reply_markup=get_sub_keyboard(settings.channel_link),
        )
        return

    # если подписан
    await show_main_menu(message)