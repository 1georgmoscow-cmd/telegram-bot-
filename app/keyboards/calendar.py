import calendar
from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


# =========================
# 📌 утилита смены месяца
# =========================
def _shift_month(base: date, offset: int) -> tuple[int, int]:
    month_index = (base.month - 1) + offset
    year = base.year + (month_index // 12)
    month = (month_index % 12) + 1
    return year, month


# =========================
# 📅 PRO календарь
# =========================
def month_calendar_kb(
    available_days: set[str],
    month_offset: int = 0,
) -> InlineKeyboardMarkup:

    today = date.today()
    max_day = today + timedelta(days=90)  # 3 месяца вперёд

    year, month = _shift_month(today, month_offset)
    cal = calendar.Calendar(firstweekday=0)

    keyboard: list[list[InlineKeyboardButton]] = []

    # 📅 заголовок
    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {calendar.month_name[month]} {year}",
            callback_data="calendar:noop",
        )
    ])

    # 📆 дни недели
    keyboard.append([
        InlineKeyboardButton(text=day, callback_data="calendar:noop")
        for day in WEEKDAYS
    ])

    # 📆 дни месяца
    for week in cal.monthdatescalendar(year, month):
        row: list[InlineKeyboardButton] = []

        for day in week:
            day_str = day.strftime("%Y-%m-%d")

            in_range = today <= day <= max_day
            is_available = day_str in available_days

            if day.month != month or not in_range:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="calendar:noop",
                    )
                )

            elif is_available:
                row.append(
                    InlineKeyboardButton(
                        text=str(day.day),
                        callback_data=f"pick_date:{day_str}",
                    )
                )

            else:
                row.append(
                    InlineKeyboardButton(
                        text=f"·{day.day}",
                        callback_data="calendar:noop",
                    )
                )

        keyboard.append(row)

    # 🔁 навигация
    nav = []

    if month_offset > 0:
        nav.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"cal_month:{month_offset - 1}",
            )
        )

    if month_offset < 2:
        nav.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"cal_month:{month_offset + 1}",
            )
        )

    if nav:
        keyboard.append(nav)

    # 🔙 меню
    keyboard.append([
        InlineKeyboardButton(text="🏠 В меню", callback_data="back_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# =========================
# ⏰ слоты времени
# =========================
def slots_kb(date_str: str, slots: list[str]) -> InlineKeyboardMarkup:
    keyboard = []

    for slot in slots:
        keyboard.append([
            InlineKeyboardButton(
                text=slot,
                callback_data=f"pick_time:{date_str}:{slot}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_calendar")
    ])

    keyboard.append([
        InlineKeyboardButton(text="🏠 В меню", callback_data="back_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# =========================
# ✅ подтверждение
# =========================
def confirm_booking_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")],
        ]
    )


# =========================
# 📅 формат даты
# =========================
def format_ru_date(date_str: str) -> str:
    return date.fromisoformat(date_str).strftime("%d.%m.%Y")
