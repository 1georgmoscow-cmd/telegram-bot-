from datetime import date, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.database.db import Database
from app.keyboards.calendar import (
    confirm_booking_kb,
    format_ru_date,
    month_calendar_kb,
    slots_kb,
)
from app.keyboards.common import back_to_menu_kb, subscription_kb
from app.services.subscription import is_subscribed
from app.states.booking import BookingStates

router = Router()


# =========================
# 📅 диапазон дат
# =========================
def get_range():
    today = date.today()
    return today.strftime("%Y-%m-%d"), (today + timedelta(days=30)).strftime("%Y-%m-%d")


# =========================
# 📅 показать календарь
# =========================
async def show_calendar(message, db: Database):
    start, end = get_range()
    days = set(db.get_month_work_days(start, end))

    if not days:
        await message.edit_text(
            "❌ Нет доступных дат",
            reply_markup=back_to_menu_kb(),
        )
        return

    await message.edit_text(
        "📅 Выбери дату:",
        reply_markup=month_calendar_kb(days),
    )


# =========================
# 🚀 КНОПКА "ЗАПИСАТЬСЯ"
# =========================
@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(
    callback: CallbackQuery, bot: Bot, settings: Settings, db: Database
):
    print("🔥 START BOOKING HANDLER WORKED")

    await callback.answer()

    # уже есть запись
    if db.has_active_booking(callback.from_user.id):
        b = db.get_active_booking(callback.from_user.id)
        await callback.message.edit_text(
            f"❗ У тебя уже есть запись:\n"
            f"{format_ru_date(b['date'])} {b['time']}",
            reply_markup=back_to_menu_kb(),
        )
        return

    # проверка подписки
    try:
        subscribed = await is_subscribed(
            bot, settings.channel_id, callback.from_user.id
        )
    except Exception as e:
        print("SUB CHECK ERROR:", e)
        subscribed = False

    if not subscribed:
        await callback.message.edit_text(
            "❗ Подпишись на канал",
            reply_markup=subscription_kb(settings.channel_link),
        )
        return

    # показываем календарь
    await show_calendar(callback.message, db)


# =========================
# 📅 выбор даты
# =========================
@router.callback_query(StateFilter(None), F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split(":")[1]
    slots = db.get_free_slots(date_str)

    if not slots:
        await callback.answer("❌ Нет слотов", show_alert=True)
        return

    await state.update_data(date=date_str)

    await callback.message.edit_text(
        f"📅 {format_ru_date(date_str)}\nВыбери время:",
        reply_markup=slots_kb(date_str, slots),
    )


# =========================
# ⏰ выбор времени
# =========================
@router.callback_query(StateFilter(None), F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, date_str, time_str = callback.data.split(":")

    await state.update_data(date=date_str, time=time_str)
    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text("✍️ Введи имя:")


# =========================
# 👤 имя
# =========================
@router.message(BookingStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer("📱 Введи телефон:")


# =========================
# 📞 телефон
# =========================
@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(phone=message.text.strip())

    await message.answer(
        f"📋 Проверь:\n\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {message.text}",
        reply_markup=confirm_booking_kb(),
    )


# =========================
# ✅ подтверждение
# =========================
@router.callback_query(F.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()

    data = await state.get_data()

    booking_id = db.create_booking(
        user_id=callback.from_user.id,
        name=data["name"],
        phone=data["phone"],
        date=data["date"],
        time=data["time"],
    )

    if not booking_id:
        await callback.message.edit_text(
            "❌ Слот уже занят",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    await state.clear()

    await callback.message.edit_text(
        "✅ Запись успешно создана!",
        reply_markup=back_to_menu_kb(),
    )
