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
from app.services.scheduler import ReminderService
from app.services.subscription import is_subscribed
from app.states.booking import BookingStates

router = Router()


def _month_range() -> tuple[str, str]:
    today = date.today()
    month_later = today + timedelta(days=31)
    return today.strftime("%Y-%m-%d"), month_later.strftime("%Y-%m-%d")


async def _show_calendar(callback: CallbackQuery, db: Database, month_offset: int = 0) -> None:
    start_date, end_date = _month_range()
    available_days = set(db.get_month_work_days(start_date, end_date))

    if not available_days:
        await callback.message.edit_text(
            "Пока нет доступных рабочих дней.",
            reply_markup=back_to_menu_kb(),
        )
        return

    await callback.message.edit_text(
        "<b>Выберите дату записи</b>",
        parse_mode="HTML",
        reply_markup=month_calendar_kb(available_days, month_offset=month_offset),
    )


# ---------------- START BOOKING ----------------

@router.callback_query(StateFilter(None), F.data == "start_booking")
async def start_booking(callback: CallbackQuery, db: Database, bot: Bot, settings: Settings) -> None:

    if db.has_active_booking(callback.from_user.id):
        booking = db.get_active_booking(callback.from_user.id)
        await callback.message.edit_text(
            "<b>У вас уже есть запись:</b>\n"
            f"Дата: <b>{format_ru_date(booking['date'])}</b>\n"
            f"Время: <b>{booking['time']}</b>",
            parse_mode="HTML",
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    subscribed = await is_subscribed(bot, settings.channel_id, callback.from_user.id)

    if not subscribed:
        await callback.message.edit_text(
            "❌ Подпишись на канал для записи",
            reply_markup=subscription_kb(settings.channel_link),
        )
        await callback.answer()
        return

    await _show_calendar(callback, db, month_offset=0)
    await callback.answer()


# ---------------- DATE ----------------

@router.callback_query(StateFilter(None), F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext) -> None:

    date_str = callback.data.split(":")[1]
    slots = db.get_free_slots(date_str)

    if not slots:
        await callback.answer("Нет свободных слотов", show_alert=True)
        return

    await state.update_data(chosen_date=date_str)

    await callback.message.edit_text(
        f"<b>Дата:</b> {format_ru_date(date_str)}\nВыберите время:",
        parse_mode="HTML",
        reply_markup=slots_kb(date_str, slots),
    )

    await callback.answer()


# ---------------- TIME ----------------

@router.callback_query(StateFilter(None), F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext) -> None:

    _, date_str, time_str = callback.data.split(":")

    await state.update_data(
        chosen_date=date_str,
        chosen_time=time_str
    )

    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text(
        f"<b>Дата:</b> {format_ru_date(date_str)}\n"
        f"<b>Время:</b> {time_str}\n\n"
        "Введите имя:",
        parse_mode="HTML",
    )

    await callback.answer()


# ---------------- NAME ----------------

@router.message(BookingStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext) -> None:

    await state.update_data(name=message.text.strip())
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer("Введите телефон:")


# ---------------- PHONE ----------------

@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext) -> None:

    phone = message.text.strip()
    data = await state.get_data()

    await state.update_data(phone=phone)

    await message.answer(
        "<b>Проверь данные:</b>\n"
        f"{format_ru_date(data['chosen_date'])} {data['chosen_time']}\n"
        f"{data['name']} | {phone}",
        parse_mode="HTML",
        reply_markup=confirm_booking_kb(),
    )


# ---------------- CONFIRM ----------------

@router.callback_query(BookingStates.waiting_for_phone, F.data == "confirm_booking")
async def confirm_booking(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
    settings: Settings,
    reminder_service: ReminderService,
) -> None:

    data = await state.get_data()

    date_str = data.get("chosen_date")
    time_str = data.get("chosen_time")
    name = data.get("name")
    phone = data.get("phone")

    if not all([date_str, time_str, name, phone]):
        await state.clear()
        await callback.message.edit_text(
            "❌ Ошибка данных, начни заново",
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    # 🔥 защита от двойного бронирования
    if db.is_slot_taken(date_str, time_str):
        await state.clear()
        await callback.message.edit_text(
            "❌ Этот слот уже занят",
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    booking_id = db.create_booking(
        user_id=callback.from_user.id,
        name=name,
        phone=phone,
        date=date_str,
        time=time_str,
    )

    if not booking_id:
        await state.clear()
        await callback.message.edit_text(
            "❌ Ошибка создания записи",
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    job_id = reminder_service.schedule_booking_reminder(
        booking_id=booking_id,
        user_id=callback.from_user.id,
        date_str=date_str,
        time_str=time_str,
    )

    db.set_reminder_job_id(booking_id, job_id)

    await state.clear()

    await callback.message.edit_text(
        "✅ Запись подтверждена!",
        reply_markup=back_to_menu_kb(),
    )

    await callback.answer()

    await callback.bot.send_message(
        settings.admin_id,
        f"Новая запись:\n{name}\n{phone}\n{date_str} {time_str}",
    )


# ---------------- MY BOOKING ----------------

@router.callback_query(F.data == "my_booking")
async def my_booking(callback: CallbackQuery, db: Database) -> None:

    booking = db.get_active_booking(callback.from_user.id)

    if not booking:
        await callback.message.edit_text(
            "Нет активной записи",
            reply_markup=back_to_menu_kb(),
        )
        return

    await callback.message.edit_text(
        f"{booking['date']} {booking['time']}\n{booking['name']}",
        reply_markup=back_to_menu_kb(),
    )


# ---------------- CANCEL ----------------

@router.callback_query(F.data == "cancel_my_booking")
async def cancel_my_booking(
    callback: CallbackQuery,
    db: Database,
    settings: Settings,
    reminder_service: ReminderService,
) -> None:

    booking = db.cancel_booking_by_user(callback.from_user.id)

    if not booking:
        await callback.message.edit_text(
            "Нет записи",
            reply_markup=back_to_menu_kb(),
        )
        return

    reminder_service.cancel_reminder(booking["reminder_job_id"])

    await callback.message.edit_text(
        "❌ Запись отменена",
        reply_markup=back_to_menu_kb(),
    )
