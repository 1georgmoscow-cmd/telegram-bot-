import time

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery

from app.services.subscription import is_subscribed
from app.handlers.ui import show_main_menu
from app.keyboards.common import subscription_kb

router = Router()

# 🚫 антиспам-кулдаун (в памяти)
CHECK_COOLDOWN = {}


@router.callback_query(F.data.in_({"check_subscription", "check_sub"}))
async def check_subscription(
    callback: CallbackQuery,
    bot: Bot,
    settings,
    db
) -> None:

    user_id = callback.from_user.id
    now = time.time()

    print("CHECK SUBSCRIPTION CLICKED")

    # 🚫 защита от спама (3 секунды)
    if user_id in CHECK_COOLDOWN:
        if now - CHECK_COOLDOWN[user_id] < 3:
            await callback.answer("Не спамь 😄 подожди пару секунд")
            return

    CHECK_COOLDOWN[user_id] = now

    await callback.answer("Проверяю подписку...")

    try:
        subscribed = await is_subscribed(
            bot,
            settings.channel_id,
            user_id
        )

        print("SUBSCRIBED RESULT:", subscribed)

        # ❌ НЕ ПОДПИСАН
        if not subscribed:
            await callback.message.edit_text(
                "❌ Ты не подписан на канал.\n\n"
                "Подпишись и нажми кнопку ещё раз.",
                reply_markup=subscription_kb(settings.channel_link)
            )
            return

        # ✅ ПОДПИСАН
        await callback.message.edit_text("⏳ Подписка подтверждена...")

        await show_main_menu(callback)

    except Exception as e:
        print("ERROR CHECK SUBSCRIPTION:", e)
        await callback.message.answer("⚠️ Ошибка проверки подписки")
