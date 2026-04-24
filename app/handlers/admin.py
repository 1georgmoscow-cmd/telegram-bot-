from datetime import date, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.repositories.booking_repo import BookingRepository
from app.keyboards.admin import admin_menu_kb, bookings_manage_kb, slots_manage_kb
from app.keyboards.calendar import format_ru_date, month_calendar_kb
from app.keyboards.common import back_to_menu_kb
from app.services.scheduler import ReminderService
from app.states.admin import AdminStates

router = Router()


# =========================
# HELPERS
# =========================
def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id == settings.admin_id


def _is_valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


# =========================
# PANEL
# =========================
@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery, settings: Settings, state: FSMContext):
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()

    await callback.message.edit_text(
        "<b>Админ-панель</b>\nВыбери действие:",
        reply_markup=admin_menu_kb(),
    )


# =========================
# ADD WORK DAY (через repo)
# =========================
@router.callback_query(F.data == "admin_add_day")
async def admin_add_day_start(callback: CallbackQuery, settings: Settings, state: FSMContext):
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_add_day)

    await callback.message.edit_text(
        "Введи дату рабочего дня: YYYY-MM-DD",
        reply_markup=back_to_menu_kb(),
    )


@router.message(AdminStates.waiting_add_day)
async def admin_add_day_save(message: Message, repo: BookingRepository, state: FSMContext):
    day = message.text.strip()

    if not _is_valid_date(day):
        await message.answer("Неверный формат даты")
        return

    # ⚠️ предполагается что метод есть в repo
    repo.add_work_day(day)

    await state.clear()
    await message.answer("Рабочий день добавлен", reply_markup=admin_menu_kb())


# =========================
# ADD SLOT
# =========================
@router.callback_query(F.data == "admin_add_slot")
async def admin_add_slot_start(callback: CallbackQuery, settings: Settings, state: FSMContext):
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_add_slot_date)

    await callback.message.edit_text("Введи дату: YYYY-MM-DD")


@router.message(AdminStates.waiting_add_slot_date)
async def admin_add_slot_get_date(message: Message, state: FSMContext):
    slot_date = message.text.strip()

    if not _is_valid_date(slot_date):
        await message.answer("Неверная дата")
        return

    await state.update_data(slot_date=slot_date)
    await state.set_state(AdminStates.waiting_add_slot_time)

    await message.answer("Введи время: HH:MM")


@router.message(AdminStates.waiting_add_slot_time)
async def admin_add_slot_save(message: Message, repo: BookingRepository, state: FSMContext):
    data = await state.get_data()

    slot_date = data["slot_date"]
    slot_time = message.text.strip()

    repo.add_slot(slot_date, slot_time)

    await state.clear()
    await message.answer("Слот добавлен", reply_markup=admin_menu_kb())


# =========================
# DELETE SLOT
# =========================
@router.callback_query(F.data == "admin_delete_slot")
async def admin_delete_slot_start(callback: CallbackQuery, settings: Settings, state: FSMContext):
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_delete_slot_date)

    await callback.message.edit_text("Введи дату: YYYY-MM-DD")


@router.message(AdminStates.waiting_delete_slot_date)
async def admin_delete_slot_date(message: Message, repo: BookingRepository, state: FSMContext):
    date_str = message.text.strip()

    if not _is_valid_date(date_str):
        await message.answer("Неверная дата")
        return

    slots = repo.get_free_slots(date_str)

    if not slots:
        await message.answer("Нет слотов", reply_markup=admin_menu_kb())
        await state.clear()
        return

    await state.clear()

    await message.answer(
        "Выбери слот:",
        reply_markup=slots_manage_kb("admin_delete_slot_pick", date_str, slots),
    )


@router.callback_query(F.data.startswith("admin_delete_slot_pick:"))
async def admin_delete_slot_pick(callback: CallbackQuery, repo: BookingRepository, settings: Settings):
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, date_str, time_str = callback.data.split(":")

    repo.delete_slot(date_str, time_str)

    await callback.message.edit_text("Слот удалён", reply_markup=admin_menu_kb())


# =========================
# VIEW SCHEDULE
# =========================
@router.callback_query(F.data == "admin_view_schedule")
async def admin_view_schedule_start(
    callback: CallbackQuery,
    settings: Settings,
    state: FSMContext,
    repo: BookingRepository,
):
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_view_schedule)

    today = date.today()
    days = set(
        repo.get_month_work_days(
            today.isoformat(),
            (today + timedelta(days=31)).isoformat(),
        )
    )

    await callback.message.edit_text(
        "Выбери дату:",
        reply_markup=month_calendar_kb(days, 0),
    )


@router.callback_query(AdminStates.waiting_view_schedule, F.data.startswith("pick_date:"))
async def admin_view_schedule_pick(
    callback: CallbackQuery,
    repo: BookingRepository,
    state: FSMContext,
):
    date_str = callback.data.split(":")[1]

    schedule = repo.get_schedule_by_date(date_str)

    if not schedule:
        await callback.message.edit_text("Нет данных", reply_markup=admin_menu_kb())
        await state.clear()
        return

    lines = [f"<b>{format_ru_date(date_str)}</b>"]

    for row in schedule:
        if row["booking_id"]:
            lines.append(f"{row['time']} — занято ({row['name']})")
        else:
            lines.append(f"{row['time']} — свободно")

    await callback.message.edit_text("\n".join(lines), reply_markup=admin_menu_kb())
    await state.clear()


# =========================
# CANCEL BOOKING
# =========================
@router.callback_query(F.data == "admin_cancel_booking")
async def admin_cancel_booking_start(callback: CallbackQuery, settings: Settings, state: FSMContext):
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_cancel_booking_date)

    await callback.message.edit_text("Введи дату: YYYY-MM-DD")


@router.message(AdminStates.waiting_cancel_booking_date)
async def admin_cancel_booking_date(message: Message, repo: BookingRepository, state: FSMContext):
    date_str = message.text.strip()

    bookings = repo.get_bookings_for_date(date_str)

    if not bookings:
        await message.answer("Нет записей", reply_markup=admin_menu_kb())
        await state.clear()
        return

    await state.clear()

    prepared = [
        {"id": b["id"], "name": b["name"], "time": b["time"]}
        for b in bookings
    ]

    await message.answer(
        "Выбери запись:",
        reply_markup=bookings_manage_kb(date_str, prepared),
    )


@router.callback_query(F.data.startswith("admin_cancel_by_id:"))
async def admin_cancel_by_id(
    callback: CallbackQuery,
    repo: BookingRepository,
    settings: Settings,
    reminder_service: ReminderService,
):
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return

    booking_id = int(callback.data.split(":")[1])

    booking = repo.cancel_booking_by_id(booking_id)

    if not booking:
        await callback.message.edit_text("Не найдено", reply_markup=admin_menu_kb())
        return

    reminder_service.cancel_reminder(booking["reminder_job_id"])

    await callback.message.edit_text("Отменено", reply_markup=admin_menu_kb())

    await callback.bot.send_message(
        booking["user_id"],
        f"❌ Запись отменена\n{booking['date']} {booking['time']}",
    )
