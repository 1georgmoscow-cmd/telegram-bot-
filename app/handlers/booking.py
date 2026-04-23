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


async def _show_calendar(callback: CallbackQuery, db: Database, month_offset: int = 0):
    start_date, end_date = _month_range()
    available_days = set(db.get_month_work_days(start_date, end_date))

    if not available_days:
        await callback.message.edit_text(
            "❌ Нет доступных дней",
            reply_markup=back_to_menu_kb(),
        )
        return

    await callback.message.edit_text(
        "<b>Выберите дату записи</b>",
        parse_mode="HTML",
        reply_markup=month_calendar_kb(available_days, month_offset),
    )


# ---------------- BOOK ENTRY ----------------

@router.callback_query(StateFilter(None), F.data == "book")
async def start_booking(
    callback: CallbackQuery,
    db: Database,
    bot: Bot,
    settings: Settings,
):
    await callback.answer()

    print("BOOK CLICKED")

    if db.has_active_booking(callback.from_user.id):
        booking = db.get_active_booking(callback.from_user.id)

        await callback.message.edit_text(
            "<b>У вас уже есть запись:</b>\n"
            f"📅 {format_ru_date(booking['date'])}\n"
            f"⏰ {booking['time']}",
            parse_mode="HTML",
            reply_markup=back_to_menu_kb(),
        )
        return

    subscribed = await is_subscribed(
        bot, settings.channel_id, callback.from_user.id
    )

    if not subscribed:
        await callback.message.edit_text(
            "❌ Подпишись на канал для записи",
            reply_markup=subscription_kb(settings.channel_link),
        )
        return

    await _show_calendar(callback, db)


# ---------------- CALENDAR ----------------

@router.callback_query(StateFilter(None), F.data.startswith("cal_month:"))
async def calendar_month(callback: CallbackQuery, db: Database):
    await callback.answer()
    month_offset = int(callback.data.split(":")[1])
    await _show_calendar(callback, db, month_offset)


@router.callback_query(StateFilter(None), F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    await callback.answer()

    date_str = callback.data.split(":")[1]
    slots = db.get_free_slots(date_str)

    if not slots:
        await callback.answer("Нет слотов", show_alert=True)
        return

    await state.update_data(chosen_date=date_str)

    await callback.message.edit_text(
        f"<b>{format_ru_date(date_str)}</b>\nВыбери время:",
        parse_mode="HTML",
        reply_markup=slots_kb(date_str, slots),
    )


@router.callback_query(StateFilter(None), F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, date_str, time_str = callback.data.split(":")

    await state.update_data(
        chosen_date=date_str,
        chosen_time=time_str,
    )

    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text(
        f"📅 {format_ru_date(date_str)}\n⏰ {time_str}\n\nВведи имя:",
        parse_mode="HTML",
    )


# ---------------- FORM ----------------

@router.message(BookingStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer("Теперь номер телефона:")


@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(phone=message.text)

    await message.answer(
        "<b>Проверь:</b>\n"
        f"📅 {format_ru_date(data['chosen_date'])}\n"
        f"⏰ {data['chosen_time']}\n"
        f"👤 {data['name']}\n"
        f"📞 {message.text}",
        parse_mode="HTML",
        reply_markup=confirm_booking_kb(),
    )


# ---------------- CONFIRM ----------------

@router.callback_query(
    BookingStates.waiting_for_phone,
    F.data == "confirm_booking",
)
async def confirm_booking(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
    settings: Settings,
    reminder_service: ReminderService,
):
    await callback.answer()

    data = await state.get_data()

    booking_id = db.create_booking(
        user_id=callback.from_user.id,
        name=data["name"],
        phone=data["phone"],
        date=data["chosen_date"],
        time=data["chosen_time"],
    )

    if not booking_id:
        await callback.message.edit_text(
            "❌ Слот занят",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    await state.clear()

    await callback.message.edit_text(
        "✅ Запись создана!",
        reply_markup=back_to_menu_kb(),
    )

    await callback.bot.send_message(
        settings.admin_id,
        f"Новая запись:\n{data}",
    )


# ---------------- MY BOOKING ----------------

@router.callback_query(F.data == "my_booking")
async def my_booking(callback: CallbackQuery, db: Database):
    await callback.answer()

    booking = db.get_active_booking(callback.from_user.id)

    if not booking:
        await callback.message.edit_text(
            "Нет записи",
            reply_markup=back_to_menu_kb(),
        )
        return

    await callback.message.edit_text(
        f"📅 {booking['date']}\n⏰ {booking['time']}",
        reply_markup=back_to_menu_kb(),
    )


# ---------------- CANCEL ----------------

@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, db: Database):
    await callback.answer()

    db.cancel_booking_by_user(callback.from_user.id)

    await callback.message.edit_text(
        "❌ Запись отменена",
        reply_markup=back_to_menu_kb(),
    )
