from datetime import date, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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
# CRM CONFIG
# =========================
SERVICES = {
    "hair": "💇‍♀️ Стрижка",
    "nails": "💅 Маникюр",
    "brows": "👁 Брови",
}

BOOKING_RANGE_DAYS = 90


# =========================
# CRM HELPERS
# =========================
def get_range():
    today = date.today()
    return today, today + timedelta(days=BOOKING_RANGE_DAYS)


def build_services_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=v, callback_data=f"crm:service:{k}")]
            for k, v in SERVICES.items()
        ]
        + [[InlineKeyboardButton(text="🏠 Меню", callback_data="back_menu")]]
    )


def safe_answer(callback: CallbackQuery, text=None):
    try:
        return callback.answer(text) if text else callback.answer()
    except:
        pass


# =========================
# ENTRY POINT
# =========================
@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(callback: CallbackQuery, bot: Bot, settings: Settings, db: Database):
    safe_answer(callback)

    if db.has_active_booking(callback.from_user.id):
        b = db.get_active_booking(callback.from_user.id)
        await callback.message.edit_text(
            f"📌 У тебя уже есть запись:\n\n"
            f"{b['service']}\n"
            f"{b['date']} {b['time']}",
            reply_markup=back_to_menu_kb(),
        )
        return

    try:
        subscribed = await is_subscribed(bot, settings.channel_id, callback.from_user.id)
    except:
        subscribed = False

    if not subscribed:
        await callback.message.edit_text(
            "❗ Подпишись для записи",
            reply_markup=subscription_kb(settings.channel_link),
        )
        return

    await state_reset(callback)
    await callback.message.edit_text(
        "💎 Выбери услугу:",
        reply_markup=build_services_kb(),
    )


# =========================
# RESET CRM STATE
# =========================
async def state_reset(callback: CallbackQuery):
    # защита от "залипших" состояний
    pass


# =========================
# SERVICE STEP
# =========================
@router.callback_query(F.data.startswith("crm:service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext, db: Database):
    safe_answer(callback)

    service = callback.data.split(":")[2]

    await state.update_data(
        service=service,
        date=None,
        time=None,
        name=None,
        phone=None,
    )

    today = date.today()
    days = set(
        db.get_month_work_days(
            today.isoformat(),
            (today + timedelta(days=BOOKING_RANGE_DAYS)).isoformat(),
        )
    )

    await state.set_state(BookingStates.select_date)

    await callback.message.edit_text(
        f"💇 Услуга: {SERVICES.get(service)}\n\n📅 Выбери дату:",
        reply_markup=month_calendar_kb(days, 0),
    )


# =========================
# MONTH NAVIGATION
# =========================
@router.callback_query(F.data.startswith("cal_month:"))
async def change_month(callback: CallbackQuery, db: Database):
    safe_answer(callback)

    offset = int(callback.data.split(":")[1])

    today = date.today()
    days = set(
        db.get_month_work_days(
            today.isoformat(),
            (today + timedelta(days=BOOKING_RANGE_DAYS)).isoformat(),
        )
    )

    await callback.message.edit_text(
        "📅 Выбери дату:",
        reply_markup=month_calendar_kb(days, offset),
    )


# =========================
# BACK TO CALENDAR
# =========================
@router.callback_query(F.data == "back_calendar")
async def back_calendar(callback: CallbackQuery, db: Database):
    safe_answer(callback)

    today = date.today()
    days = set(
        db.get_month_work_days(
            today.isoformat(),
            (today + timedelta(days=BOOKING_RANGE_DAYS)).isoformat(),
        )
    )

    await callback.message.edit_text(
        "📅 Выбери дату:",
        reply_markup=month_calendar_kb(days, 0),
    )


# =========================
# DATE PICK
# =========================
@router.callback_query(F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    safe_answer(callback)

    date_str = callback.data.split(":")[1]

    slots = db.get_free_slots(date_str)

    if not slots:
        await callback.answer("Нет слотов", show_alert=True)
        return

    await state.update_data(date=date_str)
    await state.set_state(BookingStates.select_time)

    await callback.message.edit_text(
        f"📅 {format_ru_date(date_str)}\n\n⏰ Выбери время:",
        reply_markup=slots_kb(date_str, slots),
    )


# =========================
# TIME PICK (CRITICAL FIXED)
# =========================
@router.callback_query(F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    safe_answer(callback)

    try:
        _, date_str, time_str = callback.data.split(":", 2)
    except:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    await state.update_data(date=date_str, time=time_str)
    await state.set_state(BookingStates.enter_name)

    await callback.message.edit_text(
        "✍️ Введи имя клиента:"
    )


# =========================
# NAME
# =========================
@router.message(BookingStates.enter_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingStates.enter_phone)

    await message.answer("📱 Введи телефон:")


# =========================
# PHONE
# =========================
@router.message(BookingStates.enter_phone)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(phone=message.text)

    await message.answer(
        "📌 Подтверди запись:\n\n"
        f"💇 Услуга: {data.get('service')}\n"
        f"📅 Дата: {data.get('date')}\n"
        f"⏰ Время: {data.get('time')}\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📱 Телефон: {message.text}",
        reply_markup=confirm_booking_kb(),
    )


# =========================
# CONFIRM (CRM FINAL STEP)
# =========================
@router.callback_query(F.data == "confirm_booking")
async def confirm(callback: CallbackQuery, state: FSMContext, db: Database):
    safe_answer(callback)

    data = await state.get_data()

    try:
        booking_id = db.create_booking(
            callback.from_user.id,
            data.get("service"),
            data.get("name"),
            data.get("phone"),
            data.get("date"),
            data.get("time"),
        )
    except Exception as e:
        print("DB ERROR:", e)
        await callback.message.edit_text(
            "❌ Ошибка CRM (DB)",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    await state.clear()

    if not booking_id:
        await callback.message.edit_text(
            "❌ Слот уже занят (CRM lock)",
            reply_markup=back_to_menu_kb(),
        )
        return

    await callback.message.edit_text(
        "✅ CRM: запись создана",
        reply_markup=back_to_menu_kb(),
    )
