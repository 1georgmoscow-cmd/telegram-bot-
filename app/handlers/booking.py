from datetime import date, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

from app.config import Settings
from app.repositories.booking_repo import BookingRepository
from app.keyboards.calendar import (
    month_calendar_kb,
    slots_kb,
    confirm_booking_kb,
    format_ru_date,
)
from app.keyboards.common import back_to_menu_kb, subscription_kb
from app.services.subscription import is_subscribed
from app.services.scheduler import ReminderService
from app.states.booking import BookingStates

router = Router()

SERVICES = {
    "hair": "💇‍♀️ Стрижка",
    "nails": "💅 Маникюр",
    "brows": "👁 Брови",
}


# =========================
# START
# =========================
@router.callback_query(StateFilter(None), F.data.in_(["start_booking", "book"]))
async def start_booking(
    callback: CallbackQuery,
    bot: Bot,
    settings: Settings,
    repo: BookingRepository,
):
    await callback.answer()

    # если уже есть активная запись
    if repo.has_active_booking(callback.from_user.id):
        b = repo.get_active_booking(callback.from_user.id)

        await callback.message.edit_text(
            f"📌 У тебя уже есть запись:\n\n{b['date']} {b['time']}",
            reply_markup=back_to_menu_kb(),
        )
        return

    # ✅ ПРОВЕРКА ПОДПИСКИ (ИСПРАВЛЕНО)
    subscribed = await is_subscribed(
        bot,
        settings.channel_id,
        callback.from_user.id,
    )

    if not subscribed:
        await callback.message.edit_text(
            "❗ Подпишись на канал, чтобы записаться",
            reply_markup=subscription_kb(settings.channel_link),
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
async def choose_service(
    callback: CallbackQuery,
    state: FSMContext,
    repo: BookingRepository,
):
    await callback.answer()

    service = callback.data.split(":", 1)[1]
    await state.update_data(service=service)

    today = date.today()

    days = repo.get_month_work_days(
        today.isoformat(),
        (today + timedelta(days=90)).isoformat(),
    )

    await callback.message.edit_text(
        "📅 Выбери дату:",
        reply_markup=month_calendar_kb(set(days), 0),
    )


# =========================
# PICK DATE
# =========================
@router.callback_query(F.data.startswith("pick_date:"))
async def pick_date(
    callback: CallbackQuery,
    repo: BookingRepository,
    state: FSMContext,
):
    await callback.answer()

    date_str = callback.data.split(":", 1)[1]

    slots = repo.get_free_slots(date_str)

    if not slots:
        await callback.answer("Нет доступных слотов", show_alert=True)
        return

    await state.update_data(date=date_str)

    await callback.message.edit_text(
        f"📅 {format_ru_date(date_str)}\n\nВыбери время:",
        reply_markup=slots_kb(date_str, slots),
    )


# =========================
# PICK TIME
# =========================
@router.callback_query(F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    try:
        _, date_str, time_str = callback.data.split(":", 2)
    except ValueError:
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
        "📌 Проверь данные:\n\n"
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
async def confirm(
    callback: CallbackQuery,
    state: FSMContext,
    repo: BookingRepository,
    bot: Bot,
    reminder_service: ReminderService,
):
    await callback.answer()

    data = await state.get_data()

    if not all([data.get("date"), data.get("time"), data.get("name"), data.get("phone")]):
        await callback.message.edit_text(
            "❌ Ошибка данных. Начни заново.",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    booking_id = repo.create_booking(
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

    job_id = reminder_service.schedule_booking_reminder(
        booking_id=booking_id,
        user_id=callback.from_user.id,
        date_str=data["date"],
        time_str=data["time"],
    )

    repo.set_reminder_job_id(booking_id, job_id)

    await state.clear()

    await callback.message.edit_text(
        "✅ Ты записан!",
        reply_markup=back_to_menu_kb(),
    )
