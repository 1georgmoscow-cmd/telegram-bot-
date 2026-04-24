from datetime import date, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

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
# УСЛУГИ
# =========================
SERVICES = {
    "hair": "💇‍♀️ Стрижка",
    "nails": "💅 Маникюр",
    "brows": "👁 Брови",
}


# =========================
# RANGE ДАТ
# =========================
def get_range():
    today = date.today()
    return today, today + timedelta(days=90)


# =========================
# START BOOKING
# =========================
@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(callback: CallbackQuery, bot: Bot, db: Database):
    await callback.answer()

    if db.has_active_booking(callback.from_user.id):
        b = db.get_active_booking(callback.from_user.id)
        await callback.message.edit_text(
            f"📌 У тебя уже есть запись:\n\n{b['date']} {b['time']}",
            reply_markup=back_to_menu_kb(),
        )
        return

    subscribed = await is_subscribed(bot, callback.from_user.id)
    if not subscribed:
        await callback.message.edit_text(
            "❗ Подпишись для записи",
            reply_markup=subscription_kb("https://t.me/your_channel"),
        )
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=v, callback_data=f"service:{k}")]
            for k, v in SERVICES.items()
        ]
        + [[InlineKeyboardButton(text="🏠 Меню", callback_data="back_menu")]]
    )

    await callback.message.edit_text("💎 Выбери услугу:", reply_markup=kb)


# =========================
# SERVICE
# =========================
@router.callback_query(F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()

    service = callback.data.split(":")[1]

    await state.set_state(BookingStates.choosing_date)
    await state.update_data(service=service)

    today = date.today()
    days = set(db.get_month_work_days(
        today.isoformat(),
        (today + timedelta(days=90)).isoformat()
    ))

    await callback.message.edit_text(
        "📅 Выбери дату:",
        reply_markup=month_calendar_kb(days, 0),
    )


# =========================
# MONTH SWITCH
# =========================
@router.callback_query(F.data.startswith("cal_month:"))
async def change_month(callback: CallbackQuery, db: Database):
    await callback.answer()

    offset = int(callback.data.split(":")[1])

    today = date.today()
    days = set(db.get_month_work_days(
        today.isoformat(),
        (today + timedelta(days=90)).isoformat()
    ))

    await callback.message.edit_text(
        "📅 Выбери дату:",
        reply_markup=month_calendar_kb(days, offset),
    )


# =========================
# BACK CALENDAR
# =========================
@router.callback_query(F.data == "back_calendar")
async def back_calendar(callback: CallbackQuery, db: Database):
    await callback.answer()

    today = date.today()
    days = set(db.get_month_work_days(
        today.isoformat(),
        (today + timedelta(days=90)).isoformat()
    ))

    await callback.message.edit_text(
        "📅 Выбери дату:",
        reply_markup=month_calendar_kb(days, 0),
    )


# =========================
# PICK DATE (ВАЖНО: FIX "устарело")
# =========================
@router.callback_query(BookingStates.choosing_date, F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split(":")[1]

    slots = db.get_free_slots(date_str)

    if not slots:
        await callback.answer("Нет слотов", show_alert=True)
        return

    await state.update_data(date=date_str)
    await state.set_state(BookingStates.choosing_time)

    await callback.message.edit_text(
        f"📅 {format_ru_date(date_str)}\n\nВыбери время:",
        reply_markup=slots_kb(date_str, slots),
    )


# =========================
# PICK TIME
# =========================
@router.callback_query(BookingStates.choosing_time, F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, date_str, time_str = callback.data.split(":")

    await state.update_data(date=date_str, time=time_str)
    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text("✍️ Введи имя:")


# =========================
# NAME
# =========================
@router.message(BookingStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer("📱 Введи телефон:")


# =========================
# PHONE
# =========================
@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(phone=message.text)

    await state.set_state(BookingStates.confirmation)

    await message.answer(
        "📌 Проверь:\n\n"
        f"📅 {data['date']}\n"
        f"⏰ {data['time']}\n"
        f"👤 {data['name']}\n"
        f"📱 {message.text}",
        reply_markup=confirm_booking_kb(),
    )


# =========================
# CONFIRM
# =========================
@router.callback_query(BookingStates.confirmation, F.data == "confirm_booking")
async def confirm(callback: CallbackQuery, state: FSMContext, db: Database):
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
        "✅ Ты записан!",
        reply_markup=back_to_menu_kb(),
    )
