import calendar
from datetime import date, timedelta
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


# =========================
# 📌 shift month safe
# =========================
def _shift_month(base: date, offset: int) -> tuple[int, int]:
    month_index = (base.month - 1) + offset
    year = base.year + (month_index // 12)
    month = (month_index % 12) + 1
    return year, month


# =========================
# 📅 CRM CALENDAR (FIXED)
# =========================
def month_calendar_kb(
    available_days: set[str],
    month_offset: int = 0,
) -> InlineKeyboardMarkup:

    today = date.today()
    max_day = today + timedelta(days=90)

    year, month = _shift_month(today, month_offset)
    cal = calendar.Calendar(firstweekday=0)

    keyboard: list[list[InlineKeyboardButton]] = []

    # =========================
    # 📅 HEADER
    # =========================
    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {calendar.month_name[month]} {year}",
            callback_data="noop"
        )
    ])

    # =========================
    # 📆 WEEKDAYS
    # =========================
    keyboard.append([
        InlineKeyboardButton(text=d, callback_data="noop")
        for d in WEEKDAYS
    ])

    # =========================
    # 📆 DAYS GRID
    # =========================
    for week in cal.monthdatescalendar(year, month):
        row = []

        for day in week:
            day_str = day.isoformat()

            in_range = today <= day <= max_day
            is_current_month = day.month == month
            is_available = day_str in available_days

            # пустые клетки (чужой месяц)
            if not is_current_month:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="noop"
                    )
                )
                continue

            # недоступные дни
            if not in_range:
                row.append(
                    InlineKeyboardButton(
                        text=f"·{day.day}",
                        callback_data="noop"
                    )
                )
                continue

            # доступные дни (КЛИКАБЕЛЬНЫЕ)
            if is_available:
                row.append(
                    InlineKeyboardButton(
                        text=f"{day.day}",
                        callback_data=f"pick_date:{day_str}"
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        text=f"·{day.day}",
                        callback_data="noop"
                    )
                )

        keyboard.append(row)

    # =========================
    # 🔁 NAVIGATION
    # =========================
    nav = []

    if month_offset > 0:
        nav.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"cal_month:{month_offset - 1}"
            )
        )

    if month_offset < 2:
        nav.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"cal_month:{month_offset + 1}"
            )
        )

    if nav:
        keyboard.append(nav)

    # =========================
    # 🏠 MENU
    # =========================
    keyboard.append([
        InlineKeyboardButton(
            text="🏠 В меню",
            callback_data="back_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# =========================
# ⏰ SLOTS
# =========================
def slots_kb(date_str: str, slots: list[str]) -> InlineKeyboardMarkup:
    keyboard = []

    for slot in slots:
        keyboard.append([
            InlineKeyboardButton(
                text=slot,
                callback_data=f"pick_time:{date_str}:{slot}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back_calendar"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text="🏠 В меню",
            callback_data="back_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# =========================
# ✅ CONFIRM
# =========================
def confirm_booking_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data="confirm_booking"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="back_menu"
                )
            ],
        ]
    )


# =========================
# 📅 FORMAT DATE
# =========================
def format_ru_date(date_str: str) -> str:
    try:
        return date.fromisoformat(date_str).strftime("%d.%m.%Y")
    except Exception:
        return "неверная дата"
