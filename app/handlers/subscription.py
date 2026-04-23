from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery

from app.services.subscription import is_subscribed
from app.handlers.ui import show_main_menu
from app.keyboards.common import subscription_kb

router = Router()


@router.callback_query(F.data.in_({"check_subscription", "check_sub"}))
async def check_subscription(
    callback: CallbackQuery,
    bot: Bot,
    settings,
    db
) -> None:

    print("CHECK SUBSCRIPTION CLICKED")

    await callback.answer("Проверяю подписку...")

    subscribed = await is_subscribed(
        bot,
        settings.channel_id,
        callback.from_user.id
    )

    print("SUBSCRIBED RESULT:", subscribed)

    # ❌ НЕ ПОДПИСАН
    if not subscribed:
        await callback.message.edit_text(
            "❌ Ты не подписан на канал.\n\n"
            "Подпишись и нажми кнопку «Проверить подписку» ещё раз.",
            reply_markup=subscription_kb(settings.channel_link)
        )
        return

    # ✅ ПОДПИСАН — СТАБИЛЬНЫЙ ПЕРЕХОД
    await callback.message.edit_text("⏳ Проверяю подписку...")

    await callback.answer("Подписка подтверждена ✅")

    # небольшая задержка чтобы Telegram не конфликтовал
    await show_main_menu(callback)
