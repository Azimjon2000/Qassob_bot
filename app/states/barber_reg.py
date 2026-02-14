from aiogram.fsm.state import State, StatesGroup


class BarberRegFSM(StatesGroup):
    name = State()
    phone = State()
    region = State()
    district = State()
    salon_name = State()
    photo = State()
    location = State()
    confirm = State()
