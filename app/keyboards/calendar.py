def month_calendar_kb(db, month_offset: int = 0) -> InlineKeyboardMarkup:
    today = date.today()
    max_day = today + timedelta(days=90)

    year, month = _shift_month(today, month_offset)
    cal = calendar.Calendar(firstweekday=0)

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {calendar.month_name[month]} {year}",
            callback_data="noop"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(text=d, callback_data="noop")
        for d in WEEKDAYS
    ])

    for week in cal.monthdatescalendar(year, month):
        row = []

        for day in week:
            day_str = day.isoformat()

            if day.month != month:
                row.append(InlineKeyboardButton(" ", "noop"))
                continue

            if not (today <= day <= max_day):
                row.append(InlineKeyboardButton(f"·{day.day}", "noop"))
                continue

            # 🔥 ВАЖНО: проверяем СЛОТЫ
            has_slots = len(db.get_available_slots(day_str)) > 0

            if has_slots:
                row.append(
                    InlineKeyboardButton(
                        text=str(day.day),
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

    nav = []

    if month_offset > 0:
        nav.append(InlineKeyboardButton("◀️", f"cal_month:{month_offset - 1}"))

    if month_offset < 2:
        nav.append(InlineKeyboardButton("▶️", f"cal_month:{month_offset + 1}"))

    if nav:
        keyboard.append(nav)

    keyboard.append([
        InlineKeyboardButton("🏠 В меню", callback_data="back_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
