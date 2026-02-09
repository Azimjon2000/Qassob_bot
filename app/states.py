"""FSM States for all user flows."""
from aiogram.fsm.state import State, StatesGroup


class RoleSelect(StatesGroup):
    """Role selection flow."""
    waiting_role = State()


class ClientReg(StatesGroup):
    """Client registration flow."""
    waiting_name = State()
    waiting_phone = State()
    waiting_location = State()


class ClientSearch(StatesGroup):
    """Client search flow."""
    waiting_location = State()
    waiting_search_mode = State()
    waiting_radius = State()
    waiting_region = State()
    waiting_district = State()


class ButcherReg(StatesGroup):
    """Butcher registration flow."""
    shop_name = State()
    owner_name = State()
    phone = State()
    region = State()
    district = State()
    location = State()
    work_time = State()
    image = State()
    confirm = State()


class ButcherUpdate(StatesGroup):
    """Butcher profile update flow."""
    updating_location = State()
    updating_phone = State()
    updating_prices_sell = State()
    updating_prices_buy = State()
    updating_work_time = State()
    updating_extra_info = State()
    updating_video = State()
    uploading_image = State()
    price_category = State()
    price_value = State()


class AdminBroadcast(StatesGroup):
    """Admin broadcast flow."""
    select_target = State()
    wait_content = State()
    donate_card_update_wait = State()
    donate_amount_update_wait = State()


class AdminSupport(StatesGroup):
    """Admin support reply flow."""
    reply_to_user = State()
    support_profile_update_wait = State()


class Settings(StatesGroup):
    """User settings edit flow."""
    edit_name_wait = State()
    edit_phone_wait = State()
    edit_language_wait = State()
    edit_image_wait = State()  # For butchers


class AdminAddAdmin(StatesGroup):
    """Admin add new admin flow."""
    waiting_telegram_id = State()


class AdminButcherMessage(StatesGroup):
    """Admin send message to butcher flow."""
    waiting_message = State()


class AdminDeleteUser(StatesGroup):
    """Admin delete user by telegram ID flow."""
    waiting_telegram_id = State()

