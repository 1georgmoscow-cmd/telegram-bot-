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


def get_range():
    today = date.today()
    return today.strftime("%Y-%m-%d"), (today + timedelta(days=30)).strftime("%Y-%m-%d")


async def show_calendar(message, db: Database):
    start, end = get_range()
    days = set(db.get_month_work_days(start, end))

    if not days:
        await message.edit_text(
            "Нет доступных дат.",
            reply_markup=back_to_menu_kb(),
        )
        return

    await message.edit_text(
        "📅 Выберите дату:",
        reply_markup=month_calendar_kb(days),
    )


# =========================
# 📌 КНОПКА "ЗАПИСАТЬСЯ"
# =========================
@router.callback_query(StateFilter(None), F.data == "start_booking")
async def start_booking(callback: CallbackQuery, bot: Bot, settings: Settings, db: Database):
    try:
        await callback.answer()

        # уже есть запись
        if db.has_active_booking(callback.from_user.id):
            b = db.get_active_booking(callback.from_user.id)
            await callback.message.edit_text(
                f"У вас уже есть запись:\n"
                f"{format_ru_date(b['date'])} {b['time']}",
                reply_markup=back_to_menu_kb(),
            )
            return

        # проверка подписки
        try:
            subscribed = await is_subscribed(bot, settings.channel_id, callback.from_user.id)
        except Exception:
            subscribed = False

        if not subscribed:
            await callback.message.edit_text(
                "❗ Подпишитесь на канал для записи",
                reply_markup=subscription_kb(settings.channel_link),
            )
            return

        await show_calendar(callback.message, db)

    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")


# =========================
# 📌 календарь
# =========================
@router.callback_query(StateFilter(None), F.data.startswith("pick_date:"))
async def pick_date(callback: CallbackQuery, db: Database, state: FSMContext):
    date_str = callback.data.split(":")[1]
    slots = db.get_free_slots(date_str)

    if not slots:
        await callback.answer("Нет слотов", show_alert=True)
        return

    await state.update_data(date=date_str)

    await callback.message.edit_text(
        f"Дата: {format_ru_date(date_str)}\nВыберите время:",
        reply_markup=slots_kb(date_str, slots),
    )


# =========================
# 📌 выбор времени
# =========================
@router.callback_query(StateFilter(None), F.data.startswith("pick_time:"))
async def pick_time(callback: CallbackQuery, state: FSMContext):
    _, date_str, time_str = callback.data.split(":")

    await state.update_data(date=date_str, time=time_str)
    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text("Введите имя:")


# =========================
# 📌 имя
# =========================
@router.message(BookingStates.waiting_for_name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer("Введите телефон:")


# =========================
# 📌 телефон
# =========================
@router.message(BookingStates.waiting_for_phone)
async def phone(message: Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(phone=message.text)

    await message.answer(
        f"Проверь:\n"
        f"{data['date']} {data['time']}\n"
        f"{data['name']}\n"
        f"{message.text}",
        reply_markup=confirm_booking_kb(),
    )


# =========================
# 📌 подтверждение
# =========================
@router.callback_query(F.data == "confirm_booking")
async def confirm(callback: CallbackQuery, state: FSMContext, db: Database):
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
            "Слот занят",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        return

    await state.clear()

    await callback.message.edit_text(
        "✅ Запись создана!",
        reply_markup=back_to_menu_kb(),
    )
