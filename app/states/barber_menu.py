from aiogram.fsm.state import State, StatesGroup


class BarberMenuFSM(StatesGroup):
    menu = State()
    edit_name = State()
    edit_phone = State()
    edit_location = State()
    edit_photo = State()
    price_hair = State()
    price_beard = State()
    price_groom = State()
    price_note = State()
    add_work_photo = State()
    add_work_video = State()
