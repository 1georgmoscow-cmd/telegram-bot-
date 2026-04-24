from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    # =========================
    # выбор услуги
    # =========================
    choosing_service = State()

    # =========================
    # выбор даты
    # =========================
    choosing_date = State()

    # =========================
    # выбор времени
    # =========================
    choosing_time = State()

    # =========================
    # ввод данных клиента
    # =========================
    waiting_for_name = State()
    waiting_for_phone = State()

    # =========================
    # подтверждение записи
    # =========================
    confirmation = State()
