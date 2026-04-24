@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()

    repo: BookingRepository = callback.bot["repo"]
    settings: Settings = callback.bot["settings"]

    if repo.has_active_booking(callback.from_user.id):
        b = repo.get_active_booking(callback.from_user.id)

        await callback.message.edit_text(
            f"📌 У тебя уже есть запись:\n\n{b['date']} {b['time']}",
            reply_markup=back_to_menu_kb(),
        )
        return

    subscribed = await is_subscribed(
        bot,
        settings.channel_id,
        callback.from_user.id,
    )

    if not subscribed:
        await callback.message.edit_text(
            "❗ Подпишись для записи",
            reply_markup=subscription_kb(settings.channel_link),
        )
        return
