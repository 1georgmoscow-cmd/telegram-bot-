from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery

from app.services.subscription import is_subscribed
from app.handlers.menu import show_main_menu
from app.keyboards.common import subscription_kb

router = Router()


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, bot: Bot, settings, db):

    subscribed = await is_subscribed(
        bot,
        settings.channel_id,
        callback.from_user.id
    )

    # ❌ не подписан
    if not subscribed:
        await callback.message.edit_text(
            "❌ Ты не подписан на канал.\nПодпишись и нажми кнопку ещё раз.",
            reply_markup=subscription_kb(settings.channel_link)
        )
        await callback.answer("Подписка не найдена", show_alert=True)
        return

    # ✅ подписан
    await callback.answer("Подписка подтверждена ✅")

    # 🔥 показываем главное меню
    await show_main_menu(callback)
