from aiogram.types import CallbackQuery


async def show_main_menu(target):
    text = (
        "🏠 Главное меню\n\n"
        "📅 Запись\n"
        "📖 Мои записи\n"
        "💰 Прайсы\n"
        "🖼 Портфолио\n"
        "❓ FAQ"
    )

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text)
    else:
        await target.answer(text)