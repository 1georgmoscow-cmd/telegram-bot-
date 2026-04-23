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

    # 🔍 проверяем подписку
    subscribed = await is_subscribed(
        bot,
        settings.channel_id,
        callback.from_user.id
    )

    # ❌ нет подписки
    if not subscribed:
        await callback.message.edit_text(
            "❌ Ты не подписан на канал.\n\n"
            "Подпишись и нажми кнопку ещё раз.",
            reply_markup=subscription_kb(settings.channel_link)
        )
        await callback.answer("Подписка не найдена", show_alert=True)
        return

    # ✅ есть подписка
    await callback.answer("Подписка подтверждена ✅")

    # 🏠 показываем главное меню
    await show_main_menu(callback)