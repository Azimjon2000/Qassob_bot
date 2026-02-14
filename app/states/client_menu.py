from aiogram.fsm.state import State, StatesGroup


class ClientMenuFSM(StatesGroup):
    menu = State()
    search_location = State()
    search_region = State()
    search_district = State()
    barber_card = State()
    booking_confirm = State()
    edit_name = State()
    edit_phone = State()
    rate_comment = State()
