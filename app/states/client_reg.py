from aiogram.fsm.state import State, StatesGroup


class ClientRegFSM(StatesGroup):
    name = State()
    phone = State()
