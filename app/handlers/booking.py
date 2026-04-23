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


# -------------------------
# HELPERS
# -------------------------
def _month_range():
    today = date.today()
    end = today + timedelta(days=31)
    return today.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


async def _show_calendar(message: Message, db: Database, month_offset: int = 0):
    start, end = _month_range()
    days = set(db.get_month_work_days(start, end))

    if not days:
        await message.edit_text(
            "📅 Нет доступных дат.",
            reply_markup=back_to_menu_kb(),
        )
        return

    await message.edit_text(
        "📅 <b>Выберите дату записи</b>",
        parse_mode="HTML",
        reply_markup=month_calendar_kb(days, month_offset),
    )


# -------------------------
# START BOOKING
# -------------------------
@router.callback_query(F.data == "start_booking")
async def start_booking(callback: CallbackQuery, bot: Bot, db: Database, settings: Settings):
    await callback.answer()  # ВАЖНО: всегда отвечаем

    try:
        # уже есть запись
        if db.has_active_booking(callback.from_user.id):
            booking = db.get_active_booking(callback.from_user.id)

            await callback.message.edit_text(
                "<b>У вас уже есть запись:</b>\n"
                f"Дата: {format_ru_date(booking['date'])}\n"
                f"Время: {booking['time']}",
                parse_mode="HTML",
                reply_markup=back_to_menu_kb(),
            )
            return

        # проверка подписки
        subscribed = await is_subscribed(bot, settings.channel_id, callback.from_user.id)

        if not subscribed:
            await callback.message.edit_text(
                "❗ Чтобы записаться, подпишитесь на канал:",
                reply_markup=subscription_kb(settings.channel_link),
            )
            return

        await _show_calendar(callback.message, db)

    except Exception as e:
        print("ERROR start_booking:", e)
        await callback.message.answer("⚠️ Ошибка открытия записи")


# -------------------------
# CHECK SUB (ВАЖНО FIX)
# -------------------------
@router.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery, bot: Bot, settings: Settings):
    await callback.answer()

    try:
        subscribed = await is_subscribed(bot, settings.channel_id, callback.from_user.id)

        print("CHECK SUB:", subscribed)

        if not subscribed:
            await callback.answer("❌ Вы не подписаны", show_alert=True)
            return

        await callback.message.edit_text(
            "✅ Подписка подтверждена. Теперь можно записаться.",
            reply_markup=back_to_menu_kb(),
        )

    except Exception as e:
        print("ERROR check_sub:", e)
        await callback.answer("Ошибка проверки", show_alert=True)


# -------------------------
# CALENDAR MONTH
# -------------------------
@router.callback_query(F.data.startswith("cal_month:"))
async def calendar_month(callback: CallbackQuery, db: Database):
    await callback.answer()

    try:
        offset = int(callback.data.split(":")[1])
        await _show_calendar(callback.message, db, offset)
    except Exception as e:
        print("calendar_month error:", e)


# -------------------------
# PICK DATE
# -------------------------
@router.callback_query(F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    await callback.answer()

    try:
        date_str = callback.data.split(":")[1]
        slots = db.get_free_slots(date_str)

        if not slots:
            await callback.answer("Нет слотов", show_alert=True)
            return

        await state.update_data(date=date_str)

        await callback.message.edit_text(
            f"📅 {format_ru_date(date_str)}\nВыберите время:",
            reply_markup=slots_kb(date_str, slots),
        )

    except Exception as e:
        print("pick_date error:", e)


# -------------------------
# PICK TIME
# -------------------------
@router.callback_query(F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, date_str, time_str = callback.data.split(":")

    await state.update_data(date=date_str, time=time_str)
    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text(
        f"📅 {format_ru_date(date_str)}\n⏰ {time_str}\n\nВведите имя:"
    )


# -------------------------
# NAME
# -------------------------
@router.message(BookingStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer("Введите телефон:")


# -------------------------
# PHONE
# -------------------------
@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    data = await state.get_data()

    await message.answer(
        f"📅 {data['date']}\n"
        f"⏰ {data['time']}\n"
        f"👤 {data['name']}\n"
        f"📞 {data['phone']}",
        reply_markup=confirm_booking_kb(),
    )


# -------------------------
# CONFIRM
# -------------------------
@router.callback_query(F.data == "confirm_booking")
async def confirm(callback: CallbackQuery, state: FSMContext, db: Database, reminder_service: ReminderService):
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
        await callback.message.edit_text("❌ Слот уже занят", reply_markup=back_to_menu_kb())
        return

    await state.clear()

    await callback.message.edit_text(
        "✅ Запись подтверждена",
        reply_markup=back_to_menu_kb(),
    )


# -------------------------
# MY BOOKING
# -------------------------
@router.callback_query(F.data == "my_booking")
async def my_booking(callback: CallbackQuery, db: Database):
    await callback.answer()

    booking = db.get_active_booking(callback.from_user.id)

    if not booking:
        await callback.message.edit_text("Нет записи", reply_markup=back_to_menu_kb())
        return

    await callback.message.edit_text(
        f"📅 {booking['date']}\n⏰ {booking['time']}",
        reply_markup=back_to_menu_kb(),
    )
