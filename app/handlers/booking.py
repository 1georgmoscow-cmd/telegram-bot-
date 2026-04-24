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

SERVICES = {
    "hair": "💇‍♀️ Стрижка",
    "nails": "💅 Маникюр",
    "brows": "👁 Брови",
}


def get_range():
    today = date.today()
    return today, today + timedelta(days=90)


# =========================
# SAFE EDIT (FIX CALLBACK STALE)
# =========================
async def safe_edit(callback: CallbackQuery, text: str, kb=None):
    try:
        if callback.message.text != text:
            await callback.message.edit_text(text, reply_markup=kb)
        else:
            await callback.answer()
    except:
        await callback.message.answer(text, reply_markup=kb)


# =========================
# START BOOKING
# =========================
@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(callback: CallbackQuery, bot: Bot, settings: Settings, db: Database):
    await callback.answer()

    # FIX SUBSCRIPTION
    subscribed = await is_subscribed(
        bot,
        settings.channel_id,
        callback.from_user.id
    )

    if not subscribed:
        await safe_edit(
            callback,
            "❗ Подпишись для записи",
            subscription_kb(settings.channel_link),
        )
        return

    if db.has_active_booking(callback.from_user.id):
        b = db.get_active_booking(callback.from_user.id)
        await safe_edit(
            callback,
            f"📌 У тебя уже есть запись:\n\n{b['date']} {b['time']}",
            back_to_menu_kb(),
        )
        return

    kb = await build_services_kb()
    await safe_edit(callback, "💎 Выбери услугу:", kb)


async def build_services_kb():
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=v, callback_data=f"service:{k}")]
            for k, v in SERVICES.items()
        ]
        + [[InlineKeyboardButton(text="🏠 Меню", callback_data="back_menu")]]
    )


# =========================
# SERVICE
# =========================
@router.callback_query(F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()

    service = callback.data.split(":")[1]
    await state.update_data(service=service)

    today = date.today()
    days = set(
        db.get_month_work_days(
            today.isoformat(),
            (today + timedelta(days=90)).isoformat(),
        )
    )

    await safe_edit(
        callback,
        "📅 Выбери дату:",
        month_calendar_kb(days, 0),
    )


# =========================
# MONTH NAV
# =========================
@router.callback_query(F.data.startswith("cal_month:"))
async def change_month(callback: CallbackQuery, db: Database):
    await callback.answer()

    offset = int(callback.data.split(":")[1])
    today = date.today()

    days = set(
        db.get_month_work_days(
            today.isoformat(),
            (today + timedelta(days=90)).isoformat(),
        )
    )

    await safe_edit(
        callback,
        "📅 Выбери дату:",
        month_calendar_kb(days, offset),
    )


# =========================
# PICK DATE
# =========================
@router.callback_query(F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split(":", 1)[1]

    slots = db.get_free_slots(date_str) or []

    if not slots:
        await callback.answer("Нет слотов", show_alert=True)
        return

    await state.update_data(date=date_str)

    await safe_edit(
        callback,
        f"📅 {format_ru_date(date_str)}\n\nВыбери время:",
        slots_kb(date_str, slots),
    )


# =========================
# PICK TIME
# =========================
@router.callback_query(F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, date_str, time_str = callback.data.split(":", 2)

    await state.update_data(date=date_str, time=time_str)
    await state.set_state(BookingStates.waiting_for_name)

    await safe_edit(callback, "✍️ Введи имя:")


# =========================
# NAME
# =========================
@router.message(BookingStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer("📱 Введи телефон:")


# =========================
# PHONE + CONFIRM
# =========================
@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(phone=message.text)

    await message.answer(
        "📌 Проверь:\n\n"
        f"📅 {data['date']}\n"
        f"⏰ {data['time']}\n"
        f"👤 {data['name']}\n"
        f"📱 {message.text}",
        reply_markup=confirm_booking_kb(),
    )


# =========================
# CONFIRM BOOKING
# =========================
@router.callback_query(F.data == "confirm_booking")
async def confirm(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()

    data = await state.get_data()

    if not data.get("date") or not data.get("time"):
        await callback.answer("Ошибка данных", show_alert=True)
        return
    
    booking_id = db.create_booking(
        callback.from_user.id,
        data["name"],
        data["phone"],
        data["date"],
        data["time"],
    )

    if not booking_id:
        await safe_edit(callback, "❌ Слот уже занят", back_to_menu_kb())
        await state.clear()
        return

    await state.clear()

    await safe_edit(callback, "✅ Ты записан!", back_to_menu_kb())
