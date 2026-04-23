from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery

from app.services.subscription import is_subscribed
from app.handlers.ui import show_main_menu
from app.keyboards.common import subscription_kb

router = Router()


@router.callback_query(F.data == "check_subscription")
async def check_subscription(
    callback: CallbackQuery,
    bot: Bot,
    settings,
    db
) -> None:

    print("CHECK SUBSCRIPTION CLICKED")

    # отвечаем на нажатие кнопки (убирает "часики")
    await callback.answer("Проверяю подписку...")

    # проверка подписки
    subscribed = await is_subscribed(
        bot,
        settings.channel_id,
        callback.from_user.id
    )

    print("SUBSCRIBED RESULT:", subscribed)

    # если НЕ подписан
    if not subscribed:
        await callback.message.edit_text(
            "❌ Ты не подписан на канал.\n\n"
            "Подпишись и нажми кнопку ещё раз.",
            reply_markup=subscription_kb(settings.channel_link)
        )
        return

    # если подписан
    await callback.answer("Подписка подтверждена ✅")

    await show_main_menu(callback)
