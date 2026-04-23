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
    print("CHECK SUBSCRIPTION CLICKED")
) -> None:

    print("НАЖАЛИ НА ПРОВЕРКУ ПОДПИСКИ")
    await callback.answer()

    user_id = callback.from_user.id

    subscribed = await is_subscribed(
        bot,
        settings.channel_id,
        user_id
    )

    # ❌ не подписан
    if not subscribed:
        try:
            await callback.message.edit_text(
                "❌ Ты не подписан на канал.\n\n"
                "Подпишись и нажми кнопку ещё раз.",
                reply_markup=subscription_kb(settings.channel_link)
            )
        except:
            pass

        await callback.answer("Подписка не найдена", show_alert=True)
        return

    # ✅ подписан
    await callback.answer("Подписка подтверждена ✅")

    # 🧹 удаляем сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # 🏠 меню
    await show_main_menu(callback)
