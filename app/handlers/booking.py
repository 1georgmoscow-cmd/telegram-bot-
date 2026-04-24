from datetime import date, timedelta

from aiogram import Router, F, Bot
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
# 📅 генерация дат (если БД пустая)
# =========================
def generate_days():
    today = date.today()
    return {
        (today + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, 8)  # 7 дней вперед
    }


# =========================
# 📅 показать календарь
# =========================
async def show_calendar(message, db: Database):
    try:
        start = date.today().strftime("%Y-%m-%d")
        end = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")

        days = set(db.get_month_work_days(start, end))

        # если пусто — генерим сами
        if not days:
            days = generate_days()

        await message.edit_text(
            "📅 Выбери дату:",
            reply_markup=month_calendar_kb(days),
        )

    except Exception as e:
        await message.answer(f"Ошибка календаря: {e}")


# =========================
# 🚀 КНОПКА "ЗАПИСАТЬСЯ"
# =========================
@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(
    callback: CallbackQuery,
    bot: Bot,
    settings: Settings,
    db: Database,
):
    print("BOOKING HANDLER TRIGGERED")

    await callback.answer()

    # уже есть запись
    if db.has_active_booking(callback.from_user.id):
        booking = db.get_active_booking(callback.from_user.id)

        await callback.message.edit_text(
            f"📌 У тебя уже есть запись:\n"
            f"{format_ru_date(booking['date'])} {booking['time']}",
            reply_markup=back_to_menu_kb(),
        )
        return

    # проверка подписки
    try:
        subscribed = await is_subscribed(
            bot, settings.channel_id, callback.from_user.id
        )
    except Exception:
        subscribed = False

    if not subscribed:
        await callback.message.edit_text(
            "❗ Подпишись на канал для записи",
            reply_markup=subscription_kb(settings.channel_link),
        )
        return

    await show_calendar(callback.message, db)


# =========================
# 📅 выбор даты
# =========================
@router.callback_query(F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split(":")[1]
    slots = db.get_free_slots(date_str)

    # если нет слотов — создаем фейковые
    if not slots:
        slots = ["10:00", "12:00", "14:00", "16:00"]

    await state.update_data(date=date_str)

    await callback.message.edit_text(
        f"📅 Дата: {format_ru_date(date_str)}\nВыбери время:",
        reply_markup=slots_kb(date_str, slots),
    )


# =========================
# ⏰ выбор времени
# =========================
@router.callback_query(F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, date_str, time_str = callback.data.split(":")

    await state.update_data(date=date_str, time=time_str)
    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text("Введи имя:")


# =========================
# 👤 имя
# =========================
@router.message(BookingStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer("Введи телефон:")


# =========================
# 📱 телефон
# =========================
@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(phone=message.text)

    await message.answer(
        f"Проверь:\n\n"
        f"📅 {data['date']} {data['time']}\n"
        f"👤 {data['name']}\n"
        f"📱 {message.text}",
        reply_markup=confirm_booking_kb(),
    )


# =========================
# ✅ подтверждение
# =========================
@router.callback_query(F.data == "confirm_booking")
async def confirm_booking(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
):
    await callback.answer()

    data = await state.get_data()

    booking_id = db.create_booking(
        callback.from_user.id,
        data["name"],
        data["phone"],
        data["date"],
        data["time"],
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
        "✅ Запись создана!",
        reply_markup=back_to_menu_kb(),
    )
