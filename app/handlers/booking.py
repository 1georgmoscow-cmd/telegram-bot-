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
    return today, today + timedelta(days=60)


async def safe_answer(callback: CallbackQuery):
    try:
        await callback.answer()
    except:
        pass


# =========================
# START BOOKING
# =========================
@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(callback: CallbackQuery, bot: Bot, settings: Settings, db: Database):
    await safe_answer(callback)

    if db.has_active_booking(callback.from_user.id):
        b = db.get_active_booking(callback.from_user.id)

        await callback.message.edit_text(
            f"📌 У тебя уже есть запись:\n\n"
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

    await callback.message.edit_text(
        "💎 Выбери услугу:",
        reply_markup=service_kb(),
    )


# =========================
# SERVICES KB
# =========================
def service_kb():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=v, callback_data=f"service:{k}")]
            for k, v in SERVICES.items()
        ]
        + [[InlineKeyboardButton(text="🏠 Меню", callback_data="back_menu")]]
    )


# =========================
# CHOOSE SERVICE
# =========================
@router.callback_query(F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    await safe_answer(callback)

    service = callback.data.split(":", 1)[1]
    await state.update_data(service=service)

    start, end = get_range()
    available_days = set()

    await callback.message.edit_text(
        "📅 Выбери дату:",
        reply_markup=month_calendar_kb(available_days),
    )


# =========================
# PICK DATE
# =========================
@router.callback_query(F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    await safe_answer(callback)

    date_str = callback.data.split(":", 1)[1]

    slots = db.get_free_slots(date_str)

    if not slots:
        await callback.answer("Нет свободных слотов", show_alert=True)
        return

    await state.update_data(date=date_str)

    await callback.message.edit_text(
        f"📅 {format_ru_date(date_str)}\n\nВыбери время:",
        reply_markup=slots_kb(date_str, slots),
    )


# =========================
# PICK TIME (FIXED SAFE PARSE)
# =========================
@router.callback_query(F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await safe_answer(callback)

    try:
        _, date_str, time_str = callback.data.split(":", 2)
    except ValueError:
        await callback.answer("Ошибка выбора времени", show_alert=True)
        return

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

    await message.answer(
        "📌 Проверь запись:\n\n"
        f"💎 {data.get('service')}\n"
        f"📅 {data.get('date')}\n"
        f"⏰ {data.get('time')}\n"
        f"👤 {data.get('name')}\n"
        f"📱 {message.text}",
        reply_markup=confirm_booking_kb(),
    )


# =========================
# CONFIRM
# =========================
@router.callback_query(F.data == "confirm_booking")
async def confirm(callback: CallbackQuery, state: FSMContext, db: Database):
    await safe_answer(callback)

    data = await state.get_data()

    booking_id = db.create_booking(
        callback.from_user.id,
        data.get("service"),
        data.get("name"),
        data.get("phone"),
        data.get("date"),
        data.get("time"),
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


# =========================
# BACK FIX (ВАЖНО!)
# =========================
@router.callback_query(F.data == "back_menu")
async def back_menu(callback: CallbackQuery, state: FSMContext):
    await safe_answer(callback)
    await state.clear()

    from app.handlers.ui import show_main_menu
    await show_main_menu(callback)
