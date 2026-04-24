from datetime import date, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

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
# 💎 услуги
# =========================
SERVICES = {
    "hair": "💇‍♀️ Стрижка",
    "nails": "💅 Маникюр",
    "brows": "👁 Брови",
}


# =========================
# 🔒 safe edit (фикс падений Telegram)
# =========================
async def safe_edit(message: Message, text: str, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        pass


# =========================
# 📅 диапазон дат
# =========================
def get_range():
    today = date.today()
    return today, today + timedelta(days=60)


# =========================
# 📌 старт записи
# =========================
@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(callback: CallbackQuery, bot: Bot, settings: Settings, db: Database):
    await callback.answer()

    if db.has_active_booking(callback.from_user.id):
        b = db.get_active_booking(callback.from_user.id)

        await safe_edit(
            callback.message,
            f"📌 У тебя уже есть запись:\n\n"
            f"💎 {b['name']}\n"
            f"📅 {b['date']} {b['time']}",
            back_to_menu_kb(),
        )
        return

    try:
        subscribed = await is_subscribed(bot, settings.channel_id, callback.from_user.id)
    except Exception:
        subscribed = False

    if not subscribed:
        await safe_edit(
            callback.message,
            "❗ Подпишись на канал, чтобы записаться",
            subscription_kb(settings.channel_link),
        )
        return

    await safe_edit(
        callback.message,
        "💎 Выбери услугу:",
        service_kb(),
    )


# =========================
# 📌 клавиатура услуг
# =========================
def service_kb():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"service:{key}")]
            for key, name in SERVICES.items()
        ]
        + [[InlineKeyboardButton(text="🏠 Меню", callback_data="back_menu")]]
    )


# =========================
# 📌 выбор услуги
# =========================
@router.callback_query(F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    service = callback.data.split("service:")[1]
    await state.update_data(service=service)

    start, end = get_range()

    days = set(
        (start + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range((end - start).days + 1)
    )

    await safe_edit(
        callback.message,
        "📅 Выбери дату:",
        month_calendar_kb(days),
    )


# =========================
# 📌 выбор даты
# =========================
@router.callback_query(F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split("pick_date:")[1]
    slots = db.get_free_slots(date_str)

    if not slots:
        await callback.answer("Нет слотов", show_alert=True)
        return

    await state.update_data(date=date_str)

    await safe_edit(
        callback.message,
        f"📅 {format_ru_date(date_str)}\n\n⏰ Выбери время:",
        slots_kb(date_str, slots),
    )


# =========================
# 📌 выбор времени (FIXED CRITICAL BUG)
# =========================
@router.callback_query(F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    try:
        payload = callback.data.split("pick_time:")[1]
        date_str, time_str = payload.split(":")
    except Exception:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    await state.update_data(time=time_str)
    await state.set_state(BookingStates.waiting_for_name)

    await safe_edit(callback.message, "✍️ Введи имя:")


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
        "📌 Проверь запись:\n\n"
        f"💎 {data.get('service')}\n"
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
            data.get("name"),
            data.get("phone"),
            data.get("date"),
            data.get("time"),
        )
    except Exception as e:
        print("DB ERROR:", e)
        await safe_edit(callback.message, "❌ Ошибка записи", back_to_menu_kb())
        await state.clear()
        return

    if not booking_id:
        await safe_edit(callback.message, "❌ Слот занят", back_to_menu_kb())
        await state.clear()
        return

    await state.clear()

    await safe_edit(callback.message, "✅ Ты успешно записан!", back_to_menu_kb())
