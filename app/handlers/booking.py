from datetime import date, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.database.db import Database
from app.keyboards.calendar import (
    month_calendar_kb,
    slots_kb,
    confirm_booking_kb,
    format_ru_date,
)
from app.keyboards.common import back_to_menu_kb, subscription_kb
from app.services.subscription import is_subscribed
from app.states.booking import BookingStates

router = Router()


# =========================
# 📌 утилита диапазона дат
# =========================
def get_range():
    today = date.today()
    return today, today + timedelta(days=30)


# =========================
# 📌 показ календаря
# =========================
async def show_calendar(message, db: Database):
    start, end = get_range()

    days = db.get_month_work_days(
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d"),
    )

    days = set(days) if days else set()

    if not days:
        await message.edit_text(
            "❌ Нет доступных дат",
            reply_markup=back_to_menu_kb(),
        )
        return

    await message.edit_text(
        "📅 Выберите дату:",
        reply_markup=month_calendar_kb(days),
    )


# =========================
# 📌 ЗАПИСЬ (СТАРТ)
# =========================
@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(
    callback: CallbackQuery,
    bot: Bot,
    settings: Settings,
    db: Database,
):
    await callback.answer()

    # уже есть запись
    if db.has_active_booking(callback.from_user.id):
        b = db.get_active_booking(callback.from_user.id)

        await callback.message.edit_text(
            f"📌 У тебя уже есть запись:\n\n"
            f"📅 {b['date']}\n"
            f"⏰ {b['time']}",
            reply_markup=back_to_menu_kb(),
        )
        return

    # проверка подписки
    try:
        subscribed = await is_subscribed(
            bot,
            settings.channel_id,
            callback.from_user.id,
        )
    except Exception as e:
        print("SUB CHECK ERROR:", e)
        subscribed = False

    if not subscribed:
        await callback.message.edit_text(
            "❗ Для записи нужно подписаться на канал",
            reply_markup=subscription_kb(settings.channel_link),
        )
        return

    await show_calendar(callback.message, db)


# =========================
# 📌 выбор даты
# =========================
@router.callback_query(StateFilter(None), F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    await callback.answer()

    parts = callback.data.split(":", 1)
    if len(parts) < 2:
        await callback.answer("Ошибка даты", show_alert=True)
        return

    date_str = parts[1]

    slots = db.get_free_slots(date_str)
    if not slots:
        await callback.answer("Нет слотов", show_alert=True)
        return

    await state.update_data(date=date_str)

    await callback.message.edit_text(
        f"📅 {format_ru_date(date_str)}\n\nВыберите время:",
        reply_markup=slots_kb(date_str, slots),
    )


# =========================
# 📌 выбор времени (FIXED)
# =========================
@router.callback_query(StateFilter(None), F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    try:
        # безопасный парсинг
        _, date_str, time_str = callback.data.split(":", 2)

    except ValueError:
        await callback.answer("Ошибка выбора времени", show_alert=True)
        return

    await state.update_data(date=date_str, time=time_str)
    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text("✍️ Введи имя:")


# =========================
# 📌 имя
# =========================
@router.message(BookingStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer("📱 Введи телефон:")


# =========================
# 📌 телефон
# =========================
@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(phone=message.text)

    await message.answer(
        "📌 Проверь данные:\n\n"
        f"📅 {data.get('date')}\n"
        f"⏰ {data.get('time')}\n"
        f"👤 {data.get('name')}\n"
        f"📱 {message.text}",
        reply_markup=confirm_booking_kb(),
    )


# =========================
# 📌 подтверждение
# =========================
@router.callback_query(F.data == "confirm_booking")
async def confirm(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()

    data = await state.get_data()

    try:
        booking_id = db.create_booking(
            callback.from_user.id,
            data["name"],
            data["phone"],
            data["date"],
            data["time"],
        )
    except Exception as e:
        print("DB ERROR:", e)
        await callback.message.edit_text(
            "❌ Ошибка создания записи",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    if not booking_id:
        await callback.message.edit_text(
            "❌ Этот слот уже занят",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    await state.clear()

    await callback.message.edit_text(
        "✅ Ты записан!",
        reply_markup=back_to_menu_kb(),
    )
